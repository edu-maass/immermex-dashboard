import { FC } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface TestChartProps {
  data: Array<{ name: string; value: number }>;
}

export const TestChart: FC<TestChartProps> = ({ data }) => {
  console.log('TestChart component received data:', data);
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Test Chart</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80 bg-gray-100 border-2 border-red-500">
          <p className="p-4">Test Chart Container - Height: 320px</p>
          <div className="h-64 bg-blue-100">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <XAxis dataKey="name" />
                <YAxis />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
