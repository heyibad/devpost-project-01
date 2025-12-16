import ChatSidebar from "@/components/ChatSidebar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    FileSpreadsheet,
    ExternalLink,
    CheckCircle2,
    AlertCircle,
    Loader2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

interface SpreadsheetInfo {
    id: string;
    name: string;
}

interface WorksheetInfo {
    name: string;
    index: number;
    row_count: number;
    column_count: number;
}

interface ConnectionStatus {
    is_connected: boolean;
    refresh_token?: string;
    token_expires_at?: string;
    is_token_expired?: boolean;
    inventory_workbook_id?: string;
    inventory_worksheet_name?: string;
    orders_workbook_id?: string;
    orders_worksheet_name?: string;
    last_synced_at?: string;
}

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_URL = `${API_BASE_URL}/api/v1`;

export default function InventoryConfig() {
    const [searchParams] = useSearchParams();
    const { toast } = useToast();

    const [connectionStatus, setConnectionStatus] =
        useState<ConnectionStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadingSpreadsheets, setLoadingSpreadsheets] = useState(false);
    const [spreadsheets, setSpreadsheets] = useState<SpreadsheetInfo[]>([]);
    const [inventoryWorksheets, setInventoryWorksheets] = useState<
        WorksheetInfo[]
    >([]);
    const [ordersWorksheets, setOrdersWorksheets] = useState<WorksheetInfo[]>(
        []
    );

    const [selectedInventorySpreadsheet, setSelectedInventorySpreadsheet] =
        useState("");
    const [selectedInventoryWorksheet, setSelectedInventoryWorksheet] =
        useState("");
    const [selectedOrdersSpreadsheet, setSelectedOrdersSpreadsheet] =
        useState("");
    const [selectedOrdersWorksheet, setSelectedOrdersWorksheet] = useState("");

    const [savingConfig, setSavingConfig] = useState(false);

    useEffect(() => {
        // Check for OAuth callback success/error
        const connected = searchParams.get("connected");
        const error = searchParams.get("error");

        if (connected === "success") {
            toast({
                title: "Connected Successfully",
                description:
                    "Google Sheets has been connected to your account.",
            });
        } else if (error) {
            toast({
                title: "Connection Failed",
                description: error,
                variant: "destructive",
            });
        }

        fetchConnectionStatus();
    }, [searchParams]);

    const fetchConnectionStatus = async () => {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_URL}/google-sheets/status`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (response.ok) {
                const data = await response.json();
                setConnectionStatus(data);

                // If connected, fetch spreadsheets
                if (data.is_connected && !data.is_token_expired) {
                    fetchSpreadsheets();
                }
            }
        } catch (error) {
            console.error("Failed to fetch connection status:", error);
        } finally {
            setLoading(false);
        }
    };

    const fetchSpreadsheets = async () => {
        setLoadingSpreadsheets(true);
        try {
            const token = localStorage.getItem("access_token");
            console.log("🔵 Fetching spreadsheets...");
            const response = await fetch(
                `${API_URL}/google-sheets/spreadsheets`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            console.log("🔵 Spreadsheets response status:", response.status);
            if (response.ok) {
                const data = await response.json();
                console.log("✅ Spreadsheets fetched:", data);
                setSpreadsheets(data.spreadsheets);

                if (data.spreadsheets.length === 0) {
                    toast({
                        title: "No Spreadsheets Found",
                        description: "No Google Sheets found in your account.",
                        variant: "destructive",
                    });
                }
            } else {
                const errorText = await response.text();
                console.error(
                    "❌ Failed to fetch spreadsheets:",
                    response.status,
                    errorText
                );
                toast({
                    title: "Failed to Load Spreadsheets",
                    description: `Error: ${response.status} - ${errorText}`,
                    variant: "destructive",
                });
            }
        } catch (error) {
            console.error("❌ Error fetching spreadsheets:", error);
            toast({
                title: "Failed to Load Spreadsheets",
                description: "Network error. Please check your connection.",
                variant: "destructive",
            });
        } finally {
            setLoadingSpreadsheets(false);
        }
    };

    const fetchWorksheets = async (
        spreadsheetId: string,
        type: "inventory" | "orders"
    ) => {
        try {
            const token = localStorage.getItem("access_token");
            console.log(`🔵 Fetching worksheets for ${type}:`, spreadsheetId);
            const response = await fetch(
                `${API_URL}/google-sheets/spreadsheets/${spreadsheetId}/worksheets`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            console.log(
                `🔵 Worksheets response status for ${type}:`,
                response.status
            );
            if (response.ok) {
                const data = await response.json();
                console.log(`✅ Worksheets fetched for ${type}:`, data);
                if (type === "inventory") {
                    setInventoryWorksheets(data.worksheets);
                } else {
                    setOrdersWorksheets(data.worksheets);
                }
            } else {
                const errorText = await response.text();
                console.error(
                    `❌ Failed to fetch worksheets for ${type}:`,
                    response.status,
                    errorText
                );
                toast({
                    title: "Failed to Load Worksheets",
                    description: `Error: ${response.status}`,
                    variant: "destructive",
                });
            }
        } catch (error) {
            console.error(`❌ Error fetching worksheets for ${type}:`, error);
            toast({
                title: "Failed to Load Worksheets",
                description: "Network error. Please check your connection.",
                variant: "destructive",
            });
        }
    };

    const handleConnect = async () => {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_URL}/google-sheets/auth-url`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (response.ok) {
                const data = await response.json();
                if (!data.auth_url) {
                    toast({
                        title: "Configuration Error",
                        description:
                            "Google Sheets OAuth is not configured. Please contact support.",
                        variant: "destructive",
                    });
                    return;
                }
                // Redirect to Google OAuth
                window.location.href = data.auth_url;
            } else {
                toast({
                    title: "Connection Failed",
                    description: "Failed to get authorization URL",
                    variant: "destructive",
                });
            }
        } catch (error) {
            toast({
                title: "Connection Failed",
                description: "Failed to initiate OAuth flow",
                variant: "destructive",
            });
        }
    };

    const handleSaveConfig = async () => {
        if (
            !selectedInventorySpreadsheet ||
            !selectedInventoryWorksheet ||
            !selectedOrdersSpreadsheet ||
            !selectedOrdersWorksheet
        ) {
            toast({
                title: "Missing Configuration",
                description: "Please select both inventory and orders sheets",
                variant: "destructive",
            });
            return;
        }

        setSavingConfig(true);
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_URL}/google-sheets/config`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    inventory: {
                        workbook_id: selectedInventorySpreadsheet,
                        worksheet_name: selectedInventoryWorksheet,
                    },
                    orders: {
                        workbook_id: selectedOrdersSpreadsheet,
                        worksheet_name: selectedOrdersWorksheet,
                    },
                }),
            });

            if (response.ok) {
                toast({
                    title: "Configuration Saved",
                    description:
                        "Your sheet configuration has been saved successfully",
                });
                fetchConnectionStatus();
            } else {
                throw new Error("Failed to save configuration");
            }
        } catch (error) {
            toast({
                title: "Save Failed",
                description: "Failed to save sheet configuration",
                variant: "destructive",
            });
        } finally {
            setSavingConfig(false);
        }
    };

    const isConnected =
        connectionStatus?.is_connected && !connectionStatus?.is_token_expired;
    const hasConfig =
        connectionStatus?.inventory_workbook_id &&
        connectionStatus?.orders_workbook_id;

    if (loading) {
        return (
            <div className="flex h-screen w-full">
                <ChatSidebar currentPath="/chat/inventory" />
                <main className="flex-1 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 animate-spin" />
                </main>
            </div>
        );
    }

    return (
        <div className="flex h-screen w-full">
            <ChatSidebar currentPath="/chat/inventory" />

            <main className="flex-1 overflow-y-auto bg-gradient-to-b from-background to-secondary/20 p-8 pt-16 md:pt-8">
                <div className="max-w-4xl mx-auto space-y-6">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">
                            Inventory Config
                        </h1>
                        <p className="text-muted-foreground">
                            Connect Google Sheets to manage your inventory with
                            AI assistance
                        </p>
                    </div>

                    <Card className="glass p-8 border-white/30">
                        <div className="flex flex-col items-center text-center space-y-6">
                            <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center">
                                <FileSpreadsheet className="w-10 h-10 text-primary" />
                            </div>

                            <div className="space-y-2">
                                <h2 className="text-2xl font-bold">
                                    Google Sheets Integration
                                </h2>
                                <p className="text-muted-foreground max-w-md">
                                    Use Google Sheets as your inventory
                                    management system with AI-powered stock
                                    alerts, reordering suggestions, and
                                    real-time updates.
                                </p>
                            </div>

                            {isConnected ? (
                                <div className="flex items-center gap-2 text-green-500">
                                    <CheckCircle2 className="w-5 h-5" />
                                    <span className="font-medium">
                                        Connected
                                    </span>
                                </div>
                            ) : connectionStatus?.is_connected &&
                              connectionStatus?.is_token_expired ? (
                                <div className="flex flex-col items-center gap-2">
                                    <div className="flex items-center gap-2 text-yellow-500">
                                        <AlertCircle className="w-5 h-5" />
                                        <span className="font-medium">
                                            Token Expired - Reconnection
                                            Required
                                        </span>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <AlertCircle className="w-5 h-5" />
                                    <span className="font-medium">
                                        Not Connected
                                    </span>
                                </div>
                            )}

                            {!isConnected && (
                                <Button
                                    size="lg"
                                    className="mt-4"
                                    onClick={handleConnect}
                                >
                                    <FileSpreadsheet className="w-5 h-5 mr-2" />
                                    {connectionStatus?.is_token_expired
                                        ? "Reconnect to"
                                        : "OAuth Connect to"}{" "}
                                    Spreadsheet
                                    <ExternalLink className="w-4 h-4 ml-2" />
                                </Button>
                            )}

                            {isConnected && (
                                <div className="w-full space-y-6 pt-6 border-t border-border/50">
                                    <h3 className="font-semibold text-lg">
                                        Configure Sheets
                                    </h3>

                                    {loadingSpreadsheets ? (
                                        <div className="flex items-center justify-center py-8">
                                            <Loader2 className="w-6 h-6 animate-spin text-primary" />
                                            <span className="ml-2 text-muted-foreground">
                                                Loading spreadsheets...
                                            </span>
                                        </div>
                                    ) : spreadsheets.length === 0 ? (
                                        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 text-sm">
                                            <p className="text-yellow-600 font-semibold mb-1">
                                                No Spreadsheets Found
                                            </p>
                                            <p className="text-muted-foreground">
                                                Create a Google Spreadsheet
                                                first or check your Google Drive
                                                permissions.
                                            </p>
                                        </div>
                                    ) : (
                                        <>
                                            {/* Inventory Sheet Selection */}
                                            <div className="space-y-4 text-left">
                                                <div className="space-y-2">
                                                    <Label>
                                                        Inventory Spreadsheet
                                                    </Label>
                                                    <Select
                                                        value={
                                                            selectedInventorySpreadsheet
                                                        }
                                                        onValueChange={(
                                                            value
                                                        ) => {
                                                            setSelectedInventorySpreadsheet(
                                                                value
                                                            );
                                                            setSelectedInventoryWorksheet(
                                                                ""
                                                            );
                                                            fetchWorksheets(
                                                                value,
                                                                "inventory"
                                                            );
                                                        }}
                                                    >
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="Select a spreadsheet" />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            {spreadsheets.map(
                                                                (sheet) => (
                                                                    <SelectItem
                                                                        key={
                                                                            sheet.id
                                                                        }
                                                                        value={
                                                                            sheet.id
                                                                        }
                                                                    >
                                                                        {
                                                                            sheet.name
                                                                        }
                                                                    </SelectItem>
                                                                )
                                                            )}
                                                        </SelectContent>
                                                    </Select>
                                                </div>

                                                <div className="space-y-2">
                                                    <Label>
                                                        Inventory Worksheet
                                                    </Label>
                                                    <Select
                                                        value={
                                                            selectedInventoryWorksheet
                                                        }
                                                        onValueChange={
                                                            setSelectedInventoryWorksheet
                                                        }
                                                        disabled={
                                                            !selectedInventorySpreadsheet
                                                        }
                                                    >
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="Select a worksheet" />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            {inventoryWorksheets.map(
                                                                (ws) => (
                                                                    <SelectItem
                                                                        key={
                                                                            ws.name
                                                                        }
                                                                        value={
                                                                            ws.name
                                                                        }
                                                                    >
                                                                        {
                                                                            ws.name
                                                                        }
                                                                    </SelectItem>
                                                                )
                                                            )}
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                            </div>

                                            {/* Orders Sheet Selection */}
                                            <div className="space-y-4 text-left">
                                                <div className="space-y-2">
                                                    <Label>
                                                        Orders Spreadsheet
                                                    </Label>
                                                    <Select
                                                        value={
                                                            selectedOrdersSpreadsheet
                                                        }
                                                        onValueChange={(
                                                            value
                                                        ) => {
                                                            setSelectedOrdersSpreadsheet(
                                                                value
                                                            );
                                                            setSelectedOrdersWorksheet(
                                                                ""
                                                            );
                                                            fetchWorksheets(
                                                                value,
                                                                "orders"
                                                            );
                                                        }}
                                                    >
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="Select a spreadsheet" />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            {spreadsheets.map(
                                                                (sheet) => (
                                                                    <SelectItem
                                                                        key={
                                                                            sheet.id
                                                                        }
                                                                        value={
                                                                            sheet.id
                                                                        }
                                                                    >
                                                                        {
                                                                            sheet.name
                                                                        }
                                                                    </SelectItem>
                                                                )
                                                            )}
                                                        </SelectContent>
                                                    </Select>
                                                </div>

                                                <div className="space-y-2">
                                                    <Label>
                                                        Orders Worksheet
                                                    </Label>
                                                    <Select
                                                        value={
                                                            selectedOrdersWorksheet
                                                        }
                                                        onValueChange={
                                                            setSelectedOrdersWorksheet
                                                        }
                                                        disabled={
                                                            !selectedOrdersSpreadsheet
                                                        }
                                                    >
                                                        <SelectTrigger>
                                                            <SelectValue placeholder="Select a worksheet" />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            {ordersWorksheets.map(
                                                                (ws) => (
                                                                    <SelectItem
                                                                        key={
                                                                            ws.name
                                                                        }
                                                                        value={
                                                                            ws.name
                                                                        }
                                                                    >
                                                                        {
                                                                            ws.name
                                                                        }
                                                                    </SelectItem>
                                                                )
                                                            )}
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                            </div>

                                            <Button
                                                onClick={handleSaveConfig}
                                                disabled={savingConfig}
                                                className="w-full"
                                                size="lg"
                                            >
                                                {savingConfig ? (
                                                    <>
                                                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                                        Saving...
                                                    </>
                                                ) : (
                                                    <>
                                                        <CheckCircle2 className="w-5 h-5 mr-2" />
                                                        Save Configuration
                                                    </>
                                                )}
                                            </Button>

                                            {hasConfig && (
                                                <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 text-sm text-left">
                                                    <div className="font-semibold mb-2 text-green-600">
                                                        Current Configuration:
                                                    </div>
                                                    <div className="space-y-1 text-muted-foreground">
                                                        <div>
                                                            <strong>
                                                                Inventory:
                                                            </strong>{" "}
                                                            {
                                                                connectionStatus.inventory_worksheet_name
                                                            }
                                                        </div>
                                                        <div>
                                                            <strong>
                                                                Orders:
                                                            </strong>{" "}
                                                            {
                                                                connectionStatus.orders_worksheet_name
                                                            }
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            )}

                            <div className="pt-6 border-t border-border/50 w-full">
                                <h3 className="font-semibold mb-4">
                                    Capabilities:
                                </h3>
                                <ul className="space-y-2 text-left text-sm text-muted-foreground">
                                    <li className="flex items-start gap-2">
                                        <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                        <span>
                                            Real-time inventory tracking across
                                            multiple locations
                                        </span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                        <span>
                                            Automated low stock alerts and
                                            reorder notifications
                                        </span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                        <span>
                                            AI-powered demand forecasting and
                                            stock optimization
                                        </span>
                                    </li>
                                    <li className="flex items-start gap-2">
                                        <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                        <span>
                                            Sync with sales data for automatic
                                            stock updates
                                        </span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </Card>
                </div>
            </main>
        </div>
    );
}
