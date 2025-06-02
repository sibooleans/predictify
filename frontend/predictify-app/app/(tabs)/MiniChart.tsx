import React from 'react';
import { View, Text, Dimensions } from 'react-native';
import { LineChart as RawLineChart } from 'react-native-chart-kit';

const LineChart = RawLineChart as unknown as React.FC<any>;

export default function MiniChart() {
  const screenWidth = Dimensions.get("window").width;

  const data = {
    labels: ["Mon", "Tue", "Wed", "Thu", "Fri"],
    datasets: [
      {
        data: [148, 150, 147, 151, 153],
        strokeWidth: 2,
        color: () => `rgba(0, 204, 255, 1)`
      }
    ],
    legend: ["AAPL Price"]
  };

  const chartConfig = {
    backgroundGradientFrom: "#1e1e1e",
    backgroundGradientTo: "#1e1e1e",
    color: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
    fromZero: true,
    propsForDots: {
      r: "3",
      strokeWidth: "1",
      stroke: "#00ccff"
    }
  };

  return (
    <View style={{ marginTop: 20 }}>
      <Text style={{ color: "#00ccff", fontSize: 16, marginBottom: 5 }}>
        AAPL 5-Day History
      </Text>
      <LineChart
        data={data}
        width={screenWidth - 40}
        height={180}
        chartConfig={chartConfig}
        bezier
        style={{
          borderRadius: 12
        }}
      />
    </View>
  );
}