"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Tooltip, PieChart, Pie, Cell } from "recharts";
import { Activity, HardDrive, Cpu, Server, CheckCircle2, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface SystemStats {
  status: string;
  cpu: { usage: number; cores: number };
  memory: { total: number; used: number; percent: number };
  disk: { total: number; free: number; percent: number };
  system: { os: string; node: string };
}

export default function MonitoringPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [error, setError] = useState<boolean>(false);
  const [history, setHistory] = useState<{ time: string; cpu: number; ram: number }[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Try to fetch from Backend
        const res = await fetch("http://127.0.0.1:8000/system-stats");
        if (!res.ok) throw new Error("Server error");
        
        const data: SystemStats = await res.json();
        setStats(data);
        setError(false);

        // Update Graph History
        setHistory((prev) => {
          const newPoint = {
            time: new Date().toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }),
            cpu: data.cpu.usage,
            ram: data.memory.percent,
          };
          // Keep last 20 seconds
          const newHistory = [...prev, newPoint];
          if (newHistory.length > 20) newHistory.shift(); 
          return newHistory;
        });

      } catch (err) {
        console.error("Monitoring Error:", err);
        setError(true);
      }
    };

    // Initial fetch + Interval
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  // --- ERROR STATE (Backend Offline) ---
  if (error) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center space-y-4 text-center">
        <XCircle className="h-16 w-16 text-destructive" />
        <h2 className="text-2xl font-bold">System Offline</h2>
        <p className="text-muted-foreground">
          Could not connect to the Backend Probe at port 8000.<br/>
          Please ensure your python server is running: <code>py -m uvicorn app:app --port 8000</code>
        </p>
      </div>
    );
  }

  // --- LOADING STATE ---
  if (!stats) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center space-y-4">
        <Activity className="h-12 w-12 animate-pulse text-primary" />
        <p className="text-muted-foreground">Connecting to System Probe...</p>
      </div>
    );
  }

  // --- DASHBOARD (Success) ---
  const diskData = [
    { name: "Used", value: stats.disk.percent },
    { name: "Free", value: 100 - stats.disk.percent },
  ];

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold font-headline">System Health</h1>
          <p className="text-muted-foreground">Real-time infrastructure monitoring</p>
        </div>
        <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted px-3 py-1 rounded-full border">
                <Server className="w-4 h-4" />
                {stats.system.node} ({stats.system.os})
            </div>
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 px-3 py-1 gap-1">
                <CheckCircle2 className="w-4 h-4" /> {stats.status}
            </Badge>
        </div>
      </div>

      {/* Vitals Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Load</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.cpu.usage}%</div>
            <p className="text-xs text-muted-foreground">{stats.cpu.cores} Logical Cores</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">RAM Usage</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.memory.percent}%</div>
            <p className="text-xs text-muted-foreground">{stats.memory.used}GB used of {stats.memory.total}GB</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Disk Health</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.disk.percent}%</div>
            <p className="text-xs text-muted-foreground">{stats.disk.free}GB Free Storage</p>
          </CardContent>
        </Card>
      </div>

      {/* Live Charts */}
      <div className="grid gap-4 md:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Resource Timeline (Live)</CardTitle>
            <CardDescription>Tracking CPU & RAM stability over last 60s</CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={history}>
                    <defs>
                        <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorRam" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#82ca9d" stopOpacity={0}/>
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="time" className="text-xs" />
                    <YAxis domain={[0, 100]} className="text-xs" />
                    <Tooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '8px' }} />
                    <Area type="monotone" dataKey="cpu" stroke="#8884d8" fillOpacity={1} fill="url(#colorCpu)" name="CPU %" />
                    <Area type="monotone" dataKey="ram" stroke="#82ca9d" fillOpacity={1} fill="url(#colorRam)" name="RAM %" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
            <CardHeader>
                <CardTitle>Storage Distribution</CardTitle>
                <CardDescription>Primary Partition</CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center">
                <div className="h-[250px] w-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={diskData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                <Cell fill="#ef4444" /> {/* Used: Red */}
                                <Cell fill="#22c55e" /> {/* Free: Green */}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
      </div>
    </div>
  );
}