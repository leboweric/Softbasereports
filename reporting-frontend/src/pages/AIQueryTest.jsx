import React from 'react';
import Layout from '@/components/Layout';
import QueryVariationTester from '@/components/QueryVariationTester';

export default function AIQueryTest() {
  return (
    <Layout>
      <div className="container mx-auto py-6">
        <h1 className="text-2xl font-bold mb-6">AI Query Testing</h1>
        <QueryVariationTester />
      </div>
    </Layout>
  );
}