import { useState, useEffect, useCallback } from "react";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    Link2,
    FileText,
    FileSpreadsheet,
    MessageCircle,
    ExternalLink,
    CheckCircle2,
    XCircle,
    Loader2,
    RefreshCw,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";

interface ToolStatus {
    name: string;
    icon: React.ComponentType<{ className?: string }>;
    connected: boolean;
    loading: boolean;
    configureUrl: string;
}

export default function ConnectedToolsPopup() {
    const [open, setOpen] = useState(false);
    const navigate = useNavigate();
    const [tools, setTools] = useState<ToolStatus[]>([
        {
            name: "QuickBooks",
            icon: FileText,
            connected: false,
            loading: true,
            configureUrl: "/chat/accounts",
        },
        {
            name: "Spreadsheet",
            icon: FileSpreadsheet,
            connected: false,
            loading: true,
            configureUrl: "/chat/inventory",
        },
        {
            name: "WhatsApp",
            icon: MessageCircle,
            connected: false,
            loading: true,
            configureUrl: "/chat/sales",
        },
    ]);
    const [refreshing, setRefreshing] = useState(false);

    const fetchConnectionStatus = useCallback(async () => {
        // Fetch QuickBooks status
        const fetchQuickBooks = async () => {
            try {
                const response = await api.get("/api/v1/quickbooks/status");
                return response.data?.is_connected === true;
            } catch (error) {
                console.error("Failed to fetch QuickBooks status:", error);
                return false;
            }
        };

        // Fetch Google Sheets status
        const fetchSpreadsheet = async () => {
            try {
                const response = await api.get("/api/v1/google-sheets/status");
                return (
                    response.data?.is_connected === true &&
                    !response.data?.is_token_expired
                );
            } catch (error) {
                console.error("Failed to fetch Spreadsheet status:", error);
                return false;
            }
        };

        // Fetch WhatsApp status
        const fetchWhatsApp = async () => {
            try {
                const response = await api.get("/api/v1/instance_connect");
                const data = response.data;
                return (
                    data?.is_connected === true ||
                    data?.state === "open" ||
                    data?.instance?.state === "open" ||
                    data?.raw?.instance?.state === "open"
                );
            } catch (error) {
                console.error("Failed to fetch WhatsApp status:", error);
                return false;
            }
        };

        // Fetch all statuses in parallel
        const [quickBooksConnected, spreadsheetConnected, whatsAppConnected] =
            await Promise.all([
                fetchQuickBooks(),
                fetchSpreadsheet(),
                fetchWhatsApp(),
            ]);

        setTools([
            {
                name: "QuickBooks",
                icon: FileText,
                connected: quickBooksConnected,
                loading: false,
                configureUrl: "/chat/accounts",
            },
            {
                name: "Spreadsheet",
                icon: FileSpreadsheet,
                connected: spreadsheetConnected,
                loading: false,
                configureUrl: "/chat/inventory",
            },
            {
                name: "WhatsApp",
                icon: MessageCircle,
                connected: whatsAppConnected,
                loading: false,
                configureUrl: "/chat/sales",
            },
        ]);
    }, []);

    // Fetch status on mount and when popup opens
    useEffect(() => {
        fetchConnectionStatus();
    }, [fetchConnectionStatus]);

    // Refresh when popup opens
    useEffect(() => {
        if (open) {
            fetchConnectionStatus();
        }
    }, [open, fetchConnectionStatus]);

    const handleRefresh = async () => {
        setRefreshing(true);
        setTools((prev) => prev.map((tool) => ({ ...tool, loading: true })));
        await fetchConnectionStatus();
        setRefreshing(false);
    };

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    size="icon"
                    className="glass shrink-0 relative"
                >
                    <Link2 className="w-4 h-4" />
                    {tools.filter((t) => t.connected && !t.loading).length >
                        0 && (
                        <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full" />
                    )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="glass w-80 p-4" align="end">
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-lg">
                            Connected Tools
                        </h3>
                        <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="text-xs">
                                {
                                    tools.filter(
                                        (t) => t.connected && !t.loading
                                    ).length
                                }
                                /{tools.length}
                            </Badge>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-6 w-6"
                                onClick={handleRefresh}
                                disabled={refreshing}
                            >
                                <RefreshCw
                                    className={`w-3 h-3 ${
                                        refreshing ? "animate-spin" : ""
                                    }`}
                                />
                            </Button>
                        </div>
                    </div>

                    <div className="space-y-3">
                        {tools.map((tool, idx) => (
                            <div
                                key={idx}
                                className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-card/50"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                                        <tool.icon className="w-5 h-5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="font-medium">
                                            {tool.name}
                                        </p>
                                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                            {tool.loading ? (
                                                <>
                                                    <Loader2 className="w-3 h-3 animate-spin" />
                                                    <span>Checking...</span>
                                                </>
                                            ) : tool.connected ? (
                                                <>
                                                    <CheckCircle2 className="w-3 h-3 text-green-500" />
                                                    <span className="text-green-600">
                                                        Connected
                                                    </span>
                                                </>
                                            ) : (
                                                <>
                                                    <XCircle className="w-3 h-3 text-muted-foreground" />
                                                    <span>Not configured</span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {!tool.loading && !tool.connected && (
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => {
                                            navigate(tool.configureUrl);
                                            setOpen(false);
                                        }}
                                    >
                                        <span className="mr-1">Configure</span>
                                        <ExternalLink className="w-3 h-3" />
                                    </Button>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </PopoverContent>
        </Popover>
    );
}
