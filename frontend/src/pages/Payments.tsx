import { useState, useEffect, useCallback } from 'react';
import ChatSidebar from '@/components/ChatSidebar';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  DollarSign, 
  Clock, 
  CheckCircle2, 
  RefreshCw, 
  AlertCircle, 
  Loader2,
  Receipt,
  TrendingUp,
  Users,
  CreditCard,
  Calendar,
  Hash,
  XCircle
} from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { googleSheetsApi, OrderItem, OrdersStats } from '@/lib/api';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';


export default function Payments() {
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [stats, setStats] = useState<OrdersStats>({
    total_revenue: 0,
    completed_count: 0,
    pending_count: 0,
  });
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(true);

  const formatCurrency = (amount: number) => {
    return `PKR ${amount.toLocaleString()}`;
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return dateStr;
      return date.toLocaleDateString('en-PK', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const fetchOrdersData = useCallback(async (showRefreshIndicator = false) => {
    try {
      if (showRefreshIndicator) {
        setIsRefreshing(true);
      }
      setError(null);

      const data = await googleSheetsApi.getOrdersData();
      setOrders(data.orders);
      setStats(data.stats);
      setLastSyncedAt(data.last_synced_at);
      setIsConnected(true);
    } catch (err: unknown) {
      const error = err as { response?: { status?: number; data?: { detail?: string } } };
      if (error.response?.status === 404) {
        setIsConnected(false);
        setError('Google Sheets not connected or Orders sheet not configured. Please connect your Google Sheets and configure the Orders sheet in the Inventory page.');
      } else if (error.response?.status === 400) {
        setError(error.response?.data?.detail || 'Orders sheet not configured. Please configure the Orders sheet first.');
      } else {
        setError('Failed to load orders data. Please try again.');
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial data load
  useEffect(() => {
    fetchOrdersData();
  }, [fetchOrdersData]);

  const handleRefresh = () => {
    fetchOrdersData(true);
  };

  // Calculate additional stats
  const totalOrders = orders.length;
  const failedCount = orders.filter(o => o.status === 'failed').length;
  const avgOrderValue = totalOrders > 0 ? stats.total_revenue / stats.completed_count || 0 : 0;
  const uniqueCustomers = new Set(orders.map(o => o.customer)).size;
  const paymentMethods = orders.reduce((acc, order) => {
    if (order.method) {
      acc[order.method] = (acc[order.method] || 0) + 1;
    }
    return acc;
  }, {} as Record<string, number>);
  const sortedPaymentMethods = Object.entries(paymentMethods).sort((a, b) => (b[1] as number) - (a[1] as number));
  const topPaymentMethod = sortedPaymentMethods[0]?.[0] || '-';

  const statsCards = [
    { 
      label: 'Total Revenue', 
      value: formatCurrency(stats.total_revenue), 
      icon: DollarSign,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      subtitle: `From ${stats.completed_count} completed orders`
    },
    { 
      label: 'Total Orders', 
      value: totalOrders.toString(), 
      icon: Receipt,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      subtitle: `${uniqueCustomers} unique customers`
    },
    { 
      label: 'Completed', 
      value: stats.completed_count.toString(), 
      icon: CheckCircle2,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-500/10',
      subtitle: totalOrders > 0 ? `${((stats.completed_count / totalOrders) * 100).toFixed(0)}% success rate` : 'No orders yet'
    },
    { 
      label: 'Pending', 
      value: stats.pending_count.toString(), 
      icon: Clock,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
      subtitle: 'Awaiting payment'
    },
    { 
      label: 'Failed', 
      value: failedCount.toString(), 
      icon: XCircle,
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
      subtitle: 'Cancelled/Refunded'
    },
    { 
      label: 'Avg. Order Value', 
      value: formatCurrency(avgOrderValue), 
      icon: TrendingUp,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
      subtitle: `Top method: ${topPaymentMethod}`
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen w-full">
      <ChatSidebar currentPath="/chat/payments" />

      <main className="flex-1 overflow-y-auto bg-gradient-to-b from-background to-secondary/20 p-8 pt-16 md:pt-8">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Payment Dashboard</h1>
              <p className="text-muted-foreground flex items-center gap-2">
                <Receipt className="w-4 h-4" />
                Track and manage all your payment transactions
                {lastSyncedAt && (
                  <span className="text-xs bg-secondary px-2 py-1 rounded-full">
                    Last synced: {new Date(lastSyncedAt).toLocaleString()}
                  </span>
                )}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Syncing...' : 'Refresh'}
            </Button>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 className="w-10 h-10 animate-spin text-primary mb-4" />
              <span className="text-lg">Loading orders data...</span>
              <span className="text-sm text-muted-foreground">Fetching from Google Sheets</span>
            </div>
          ) : (
            <>
              {/* Stats Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                {statsCards.map((stat, idx) => (
                  <Card key={idx} className="glass p-4 border-white/30 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                        <stat.icon className={`w-5 h-5 ${stat.color}`} />
                      </div>
                    </div>
                    <p className="text-2xl font-bold">{stat.value}</p>
                    <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                    <p className="text-xs text-muted-foreground/70 mt-1">{stat.subtitle}</p>
                  </Card>
                ))}
              </div>

              {/* Summary Cards Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Payment Methods Breakdown */}
                <Card className="glass border-white/30 p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <CreditCard className="w-5 h-5 text-primary" />
                    <h3 className="font-semibold">Payment Methods</h3>
                  </div>
                  {Object.keys(paymentMethods).length === 0 ? (
                    <p className="text-sm text-muted-foreground">No payment data available</p>
                  ) : (
                    <div className="space-y-3">
                      {sortedPaymentMethods
                        .slice(0, 5)
                        .map(([method, count]) => (
                          <div key={method} className="flex items-center justify-between">
                            <span className="text-sm font-medium">{method || 'Unknown'}</span>
                            <div className="flex items-center gap-2">
                              <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-primary rounded-full"
                                  style={{ width: `${((count as number) / totalOrders) * 100}%` }}
                                />
                              </div>
                              <span className="text-sm text-muted-foreground w-8">{count}</span>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </Card>

                {/* Quick Stats */}
                <Card className="glass border-white/30 p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp className="w-5 h-5 text-primary" />
                    <h3 className="font-semibold">Quick Insights</h3>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <Users className="w-4 h-4 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">Unique Customers</span>
                      </div>
                      <p className="text-xl font-bold">{uniqueCustomers}</p>
                    </div>
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <TrendingUp className="w-4 h-4 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">Success Rate</span>
                      </div>
                      <p className="text-xl font-bold">
                        {totalOrders > 0 ? `${((stats.completed_count / totalOrders) * 100).toFixed(0)}%` : '0%'}
                      </p>
                    </div>
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <DollarSign className="w-4 h-4 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">Avg. Order</span>
                      </div>
                      <p className="text-xl font-bold">{formatCurrency(avgOrderValue)}</p>
                    </div>
                    <div className="p-3 bg-secondary/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <CreditCard className="w-4 h-4 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">Top Method</span>
                      </div>
                      <p className="text-xl font-bold truncate">{topPaymentMethod}</p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Transactions Table */}
              <Card className="glass border-white/30">
                <div className="p-6 border-b border-border/50 flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold">All Transactions</h2>
                    <p className="text-sm text-muted-foreground">{totalOrders} total orders</p>
                  </div>
                </div>
                {orders.length === 0 ? (
                  <div className="p-12 text-center">
                    <Receipt className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
                    <p className="text-lg font-medium text-muted-foreground">
                      {isConnected 
                        ? 'No orders found'
                        : 'Google Sheets not connected'
                      }
                    </p>
                    <p className="text-sm text-muted-foreground/70">
                      {isConnected 
                        ? 'Add orders to your Google Sheets Orders sheet to see them here.'
                        : 'Connect your Google Sheets to view orders data.'
                      }
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-secondary/30">
                          <TableHead className="w-[80px]">
                            <div className="flex items-center gap-1">
                              <Hash className="w-3 h-3" />
                              ID
                            </div>
                          </TableHead>
                          <TableHead>
                            <div className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              Date
                            </div>
                          </TableHead>
                          <TableHead>
                            <div className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              Customer
                            </div>
                          </TableHead>
                          <TableHead>
                            <div className="flex items-center gap-1">
                              <DollarSign className="w-3 h-3" />
                              Amount
                            </div>
                          </TableHead>
                          <TableHead>
                            <div className="flex items-center gap-1">
                              <CreditCard className="w-3 h-3" />
                              Method
                            </div>
                          </TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {orders.map((order) => (
                          <TableRow key={order.id} className="hover:bg-secondary/20 transition-colors">
                            <TableCell className="font-mono text-xs text-muted-foreground">
                              #{order.id}
                            </TableCell>
                            <TableCell>
                              <span className="text-sm">{formatDate(order.date)}</span>
                            </TableCell>
                            <TableCell>
                              <span className="font-medium">{order.customer || '-'}</span>
                            </TableCell>
                            <TableCell>
                              <span className="font-semibold">
                                {order.amount_display || formatCurrency(order.amount)}
                              </span>
                            </TableCell>
                            <TableCell>
                              <span className="text-sm">{order.method || '-'}</span>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                {getStatusIcon(order.status)}
                                <Badge
                                  variant={
                                    order.status === 'completed'
                                      ? 'default'
                                      : order.status === 'failed'
                                      ? 'destructive'
                                      : 'secondary'
                                  }
                                  className="capitalize"
                                >
                                  {order.status}
                                </Badge>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </Card>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
