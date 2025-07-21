import React from 'react'

export const LoadingSpinner = ({ 
  title = "Loading", 
  description = "Please wait...",
  size = "large",
  showProgress = false 
}) => {
  const sizeClasses = {
    small: "h-8 w-8",
    medium: "h-12 w-12", 
    large: "h-16 w-16",
    xlarge: "h-24 w-24"
  }
  
  const spinnerSize = sizeClasses[size] || sizeClasses.large
  
  return (
    <div className="min-h-[50vh] flex items-center justify-center p-8">
      <div className="text-center space-y-4">
        {/* Spinner */}
        <div className="relative inline-block">
          <div className={`${spinnerSize} rounded-full border-4 border-gray-200`}></div>
          <div className={`absolute top-0 left-0 ${spinnerSize} rounded-full border-4 border-blue-600 border-t-transparent animate-spin`}></div>
        </div>
        
        {/* Text */}
        <div className="space-y-1">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
        
        {/* Optional progress bar */}
        {showProgress && (
          <div className="w-48 mx-auto bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div className="bg-blue-600 h-full rounded-full animate-pulse" style={{ width: '60%' }}></div>
          </div>
        )}
      </div>
    </div>
  )
}

export const LoadingDots = () => {
  return (
    <div className="flex space-x-1">
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
    </div>
  )
}