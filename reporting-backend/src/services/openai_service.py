import openai
import json
import re
from datetime import datetime, timedelta
from src.config.openai_config import OpenAIConfig

class OpenAIQueryService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=OpenAIConfig.OPENAI_API_KEY)
        self.config = OpenAIConfig()
    
    def process_natural_language_query(self, query, user_context=None):
        """
        Process a natural language query and convert it to structured database query
        """
        try:
            # Validate query length
            if len(query) > self.config.MAX_QUERY_LENGTH:
                return {
                    "success": False,
                    "error": f"Query too long. Maximum {self.config.MAX_QUERY_LENGTH} characters allowed."
                }
            
            # Prepare the prompt
            system_prompt = self.config.get_system_prompt()
            
            user_prompt = f"""
            User query: "{query}"
            
            Please analyze this query and provide a structured response for querying a forklift dealership database.
            """
            
            # Add user context if available
            if user_context:
                user_prompt += f"\nUser context: {json.dumps(user_context)}"
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.config.OPENAI_MAX_TOKENS,
                temperature=self.config.OPENAI_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content
            parsed_response = json.loads(ai_response)
            
            # Enhance the response with additional processing
            enhanced_response = self._enhance_query_response(parsed_response, query)
            
            return {
                "success": True,
                "query_analysis": enhanced_response,
                "original_query": query,
                "processing_time": response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse AI response: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing query: {str(e)}"
            }
    
    def _enhance_query_response(self, ai_response, original_query):
        """Enhance the AI response with additional processing"""
        try:
            # Add confidence score based on query complexity
            confidence = self._calculate_confidence(ai_response, original_query)
            ai_response["confidence"] = confidence
            
            # Add suggested SQL fragments if applicable
            if "filters" in ai_response:
                ai_response["sql_fragments"] = self._generate_sql_fragments(ai_response["filters"])
            
            # Add data validation suggestions
            ai_response["validation_notes"] = self._generate_validation_notes(ai_response)
            
            # Add related queries suggestions
            ai_response["related_queries"] = self._suggest_related_queries(ai_response)
            
            return ai_response
            
        except Exception as e:
            # Return original response if enhancement fails
            ai_response["enhancement_error"] = str(e)
            return ai_response
    
    def _calculate_confidence(self, response, query):
        """Calculate confidence score for the query analysis"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if specific tables are identified
        if "tables" in response and len(response["tables"]) > 0:
            confidence += 0.2
        
        # Increase confidence if filters are specific
        if "filters" in response and len(response["filters"]) > 0:
            confidence += 0.2
        
        # Increase confidence if query type is clear
        if "query_type" in response and response["query_type"] in ["aggregation", "list", "count", "analysis"]:
            confidence += 0.1
        
        # Decrease confidence for very short or very long queries
        query_length = len(query.split())
        if query_length < 3 or query_length > 20:
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def _generate_sql_fragments(self, filters):
        """Generate SQL fragments based on filters"""
        fragments = []
        
        for field, condition in filters.items():
            if "date" in field.lower():
                # Handle date filters
                if condition in self.config.DATE_PATTERNS:
                    fragments.append(f"{field} {self.config.DATE_PATTERNS[condition]}")
                else:
                    fragments.append(f"{field} = '{condition}'")
            else:
                # Handle other filters
                if isinstance(condition, str):
                    fragments.append(f"{field} LIKE '%{condition}%'")
                else:
                    fragments.append(f"{field} = {condition}")
        
        return fragments
    
    def _generate_validation_notes(self, response):
        """Generate validation notes for the query"""
        notes = []
        
        if "tables" in response:
            for table in response["tables"]:
                if table.upper() not in ["CUSTOMERS", "INVENTORY", "SALES", "RENTALS", "PARTS_ORDERS", "SERVICE_TICKETS", "EMPLOYEES"]:
                    notes.append(f"Warning: Table '{table}' may not exist in the schema")
        
        if "query_type" in response and response["query_type"] == "aggregation":
            notes.append("This query requires aggregation - ensure proper GROUP BY clauses")
        
        if "filters" in response and len(response["filters"]) == 0:
            notes.append("No filters specified - query may return large result set")
        
        return notes
    
    def _suggest_related_queries(self, response):
        """Suggest related queries based on the analysis"""
        suggestions = []
        
        if "tables" in response:
            for table in response["tables"]:
                table_lower = table.lower()
                if table_lower in self.config.QUERY_SUGGESTIONS:
                    suggestions.extend(self.config.QUERY_SUGGESTIONS[table_lower][:2])
        
        # Remove duplicates and limit to 3 suggestions
        return list(set(suggestions))[:3]
    
    def get_query_suggestions(self, category=None):
        """Get query suggestions by category"""
        if category and category.lower() in self.config.QUERY_SUGGESTIONS:
            return self.config.QUERY_SUGGESTIONS[category.lower()]
        
        # Return all suggestions grouped by category
        return self.config.QUERY_SUGGESTIONS
    
    def explain_query_result(self, query, result_data, query_analysis):
        """Generate a natural language explanation of query results"""
        try:
            if not result_data:
                return "No data found matching your query criteria."
            
            # Prepare explanation prompt
            explanation_prompt = f"""
            Original query: "{query}"
            Query analysis: {json.dumps(query_analysis)}
            Result data (first 5 rows): {json.dumps(result_data[:5])}
            Total rows: {len(result_data)}
            
            Please provide a clear, concise explanation of these results in natural language.
            Focus on key insights and patterns. Keep it under 200 words.
            """
            
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that explains database query results in plain English."},
                    {"role": "user", "content": explanation_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Results found: {len(result_data)} records. Unable to generate detailed explanation: {str(e)}"
    
    def validate_api_key(self):
        """Validate that the OpenAI API key is working"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False

