import ChatSidebar from "@/components/ChatSidebar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    FileText,
    ExternalLink,
    CheckCircle2,
    AlertCircle,
    Loader2,
    XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

interface ConnectionStatus {
    is_connected: boolean;
    connection_expired?: boolean; // NEW: True if connection exists but expired
    company_name?: string;
    company_country?: string;
    company_currency?: string;
    realm_id?: string;
    last_synced_at?: string;
    connected_at?: string;
}

interface CompanyInfo {
    company_name: string;
    legal_name?: string;
    country?: string;
    email?: string;
    phone?: string;
    fiscal_year_start_month?: string;
}

interface CompanyInfoError {
    detail: string;
}

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_URL = `${API_BASE_URL}/api/v1`;

export default function AccountsConfig() {
    const [searchParams] = useSearchParams();
    const [connectionStatus, setConnectionStatus] =
        useState<ConnectionStatus | null>(null);
    const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [connecting, setConnecting] = useState(false);
    const [disconnecting, setDisconnecting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [connectionExpired, setConnectionExpired] = useState(false); // NEW: Track if connection expired

    // Check connection status on mount
    useEffect(() => {
        checkConnectionStatus();

        // Check for OAuth callback status
        const connected = searchParams.get("connected");
        const message = searchParams.get("message");

        if (connected === "success") {
            setError(null);
            // Refresh connection status after successful connection
            setTimeout(() => checkConnectionStatus(), 500);
        } else if (connected === "error") {
            setError(message || "Failed to connect to QuickBooks");
        }
    }, [searchParams]);

    // Fetch company info when connected
    useEffect(() => {
        if (connectionStatus?.is_connected) {
            fetchCompanyInfo();
        }
    }, [connectionStatus?.is_connected]);

    const checkConnectionStatus = async () => {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_URL}/quickbooks/status`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error("Failed to check connection status");
            }

            const data = await response.json();
            setConnectionStatus(data);

            // Set expired flag from backend response
            if (data.connection_expired) {
                setConnectionExpired(true);
                setError(
                    "Your QuickBooks connection has expired. Please reconnect to continue."
                );
            } else {
                setConnectionExpired(false);
                setError(null);
            }
        } catch (err) {
            console.error("Error checking connection:", err);
            setError("Failed to check connection status");
        } finally {
            setLoading(false);
        }
    };

    const fetchCompanyInfo = async () => {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_URL}/quickbooks/company-info`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (response.status === 401) {
                // Connection expired - refresh token invalid
                const errorData: CompanyInfoError = await response.json();
                if (errorData.detail?.includes("expired")) {
                    setConnectionExpired(true);
                    setError(
                        "Your QuickBooks connection has expired. Please reconnect to continue."
                    );
                }
                return;
            }

            if (!response.ok) {
                throw new Error("Failed to fetch company info");
            }

            const data = await response.json();
            setCompanyInfo(data);
            setConnectionExpired(false); // Connection is working
        } catch (err) {
            console.error("Error fetching company info:", err);
        }
    };

    const handleConnect = async () => {
        setConnecting(true);
        setError(null);
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_URL}/quickbooks/auth-url`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error("Failed to get authorization URL");
            }

            const data = await response.json();
            if (!data.auth_url) {
                setError(
                    "QuickBooks OAuth is not configured. Please contact support."
                );
                setConnecting(false);
                return;
            }
            // Redirect to QuickBooks OAuth page
            window.location.href = data.auth_url;
        } catch (err) {
            console.error("Error connecting:", err);
            setError("Failed to initiate QuickBooks connection");
            setConnecting(false);
        }
    };

    const handleDisconnect = async () => {
        if (!confirm("Are you sure you want to disconnect from QuickBooks?")) {
            return;
        }

        setDisconnecting(true);
        setError(null);
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_URL}/quickbooks/disconnect`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                throw new Error("Failed to disconnect");
            }

            // Refresh connection status
            await checkConnectionStatus();
            setCompanyInfo(null);
        } catch (err) {
            console.error("Error disconnecting:", err);
            setError("Failed to disconnect from QuickBooks");
        } finally {
            setDisconnecting(false);
        }
    };

    const isConnected = connectionStatus?.is_connected || false;

    return (
        <div className="flex h-screen w-full">
            <ChatSidebar currentPath="/chat/accounts" />

            <main className="flex-1 overflow-y-auto bg-gradient-to-b from-background to-secondary/20 p-8 pt-16 md:pt-8">
                <div className="max-w-4xl mx-auto space-y-6">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">
                            Accounts Agent Config
                        </h1>
                        <p className="text-muted-foreground">
                            Connect QuickBooks to automate your accounting and
                            bookkeeping
                        </p>
                    </div>

                    {error && (
                        <Card className="glass p-4 border-red-500/30 bg-red-500/10">
                            <div className="flex items-center gap-2 text-red-500">
                                <AlertCircle className="w-5 h-5" />
                                <span>{error}</span>
                            </div>
                        </Card>
                    )}

                    <Card className="glass p-8 border-white/30">
                        {loading ? (
                            <div className="flex flex-col items-center justify-center py-12">
                                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                                <p className="mt-4 text-muted-foreground">
                                    Checking connection status...
                                </p>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center text-center space-y-6">
                                <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center">
                                    <FileText className="w-10 h-10 text-primary" />
                                </div>

                                <div className="space-y-2">
                                    <h2 className="text-2xl font-bold">
                                        QuickBooks Integration
                                    </h2>
                                    <p className="text-muted-foreground max-w-md">
                                        Seamlessly sync your financial data with
                                        QuickBooks for automatic bookkeeping,
                                        invoicing, and financial reporting.
                                    </p>
                                </div>

                                {isConnected ? (
                                    <div className="w-full space-y-4">
                                        <div className="flex items-center gap-2 text-green-500 justify-center">
                                            <CheckCircle2 className="w-5 h-5" />
                                            <span className="font-medium">
                                                Connected
                                            </span>
                                        </div>

                                        {companyInfo && (
                                            <div className="bg-primary/5 rounded-lg p-4 space-y-2">
                                                <h3 className="font-semibold text-lg">
                                                    Company Details
                                                </h3>
                                                <div className="grid grid-cols-2 gap-3 text-sm text-left">
                                                    <div>
                                                        <span className="text-muted-foreground">
                                                            Company Name:
                                                        </span>
                                                        <p className="font-medium">
                                                            {
                                                                companyInfo.company_name
                                                            }
                                                        </p>
                                                    </div>
                                                    {companyInfo.legal_name && (
                                                        <div>
                                                            <span className="text-muted-foreground">
                                                                Legal Name:
                                                            </span>
                                                            <p className="font-medium">
                                                                {
                                                                    companyInfo.legal_name
                                                                }
                                                            </p>
                                                        </div>
                                                    )}
                                                    {companyInfo.country && (
                                                        <div>
                                                            <span className="text-muted-foreground">
                                                                Country:
                                                            </span>
                                                            <p className="font-medium">
                                                                {
                                                                    companyInfo.country
                                                                }
                                                            </p>
                                                        </div>
                                                    )}
                                                    {companyInfo.email && (
                                                        <div>
                                                            <span className="text-muted-foreground">
                                                                Email:
                                                            </span>
                                                            <p className="font-medium">
                                                                {
                                                                    companyInfo.email
                                                                }
                                                            </p>
                                                        </div>
                                                    )}
                                                    {companyInfo.phone && (
                                                        <div>
                                                            <span className="text-muted-foreground">
                                                                Phone:
                                                            </span>
                                                            <p className="font-medium">
                                                                {
                                                                    companyInfo.phone
                                                                }
                                                            </p>
                                                        </div>
                                                    )}
                                                    {connectionStatus?.realm_id && (
                                                        <div>
                                                            <span className="text-muted-foreground">
                                                                Realm ID:
                                                            </span>
                                                            <p className="font-medium font-mono text-xs">
                                                                {
                                                                    connectionStatus.realm_id
                                                                }
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                                {connectionStatus?.last_synced_at && (
                                                    <p className="text-xs text-muted-foreground pt-2">
                                                        Last synced:{" "}
                                                        {new Date(
                                                            connectionStatus.last_synced_at
                                                        ).toLocaleString()}
                                                    </p>
                                                )}
                                            </div>
                                        )}

                                        <Button
                                            size="lg"
                                            variant="destructive"
                                            className="mt-4"
                                            onClick={handleDisconnect}
                                            disabled={disconnecting}
                                        >
                                            {disconnecting ? (
                                                <>
                                                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                                    Disconnecting...
                                                </>
                                            ) : (
                                                <>
                                                    <XCircle className="w-5 h-5 mr-2" />
                                                    Disconnect QuickBooks
                                                </>
                                            )}
                                        </Button>
                                    </div>
                                ) : (
                                    <>
                                        <div className="flex items-center gap-2 text-muted-foreground">
                                            <AlertCircle className="w-5 h-5" />
                                            <span className="font-medium">
                                                {connectionExpired
                                                    ? "Connection Expired"
                                                    : "Not Connected"}
                                            </span>
                                        </div>

                                        {connectionExpired && (
                                            <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4 max-w-md">
                                                <p className="text-sm text-orange-600 dark:text-orange-400">
                                                    <strong>
                                                        Connection Expired:
                                                    </strong>{" "}
                                                    Your QuickBooks
                                                    authorization has expired
                                                    (refresh token typically
                                                    lasts ~100 days). Please
                                                    reconnect to restore access.
                                                </p>
                                            </div>
                                        )}

                                        <Button
                                            size="lg"
                                            className="mt-4"
                                            onClick={handleConnect}
                                            disabled={connecting}
                                        >
                                            {connecting ? (
                                                <>
                                                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                                    Connecting...
                                                </>
                                            ) : (
                                                <>
                                                    <FileText className="w-5 h-5 mr-2" />
                                                    {connectionExpired
                                                        ? "Reconnect"
                                                        : "Connect to"}{" "}
                                                    QuickBooks
                                                    <ExternalLink className="w-4 h-4 ml-2" />
                                                </>
                                            )}
                                        </Button>
                                    </>
                                )}

                                <div className="pt-6 border-t border-border/50 w-full">
                                    <h3 className="font-semibold mb-4">
                                        Features:
                                    </h3>
                                    <ul className="space-y-2 text-left text-sm text-muted-foreground">
                                        <li className="flex items-start gap-2">
                                            <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                            <span>
                                                Automatic transaction recording
                                                and categorization
                                            </span>
                                        </li>
                                        <li className="flex items-start gap-2">
                                            <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                            <span>
                                                Real-time financial reports and
                                                insights
                                            </span>
                                        </li>
                                        <li className="flex items-start gap-2">
                                            <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                            <span>
                                                Invoice generation and payment
                                                tracking
                                            </span>
                                        </li>
                                        <li className="flex items-start gap-2">
                                            <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                            <span>
                                                Tax calculation and compliance
                                                support
                                            </span>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        )}
                    </Card>
                </div>
            </main>
        </div>
    );
}
