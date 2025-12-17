import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import {
    adminApi,
    type DashboardStats,
    type WaitlistUser,
    type AdminUser,
} from "@/lib/api";
import {
    Users,
    UserCheck,
    Clock,
    MessageSquare,
    MessagesSquare,
    TrendingUp,
    Calendar,
    CalendarDays,
    Search,
    Loader2,
    CheckCircle2,
    XCircle,
    Shield,
    Mail,
    MailX,
    ChevronLeft,
    ChevronRight,
    RefreshCw,
    ArrowUpRight,
    Sparkles,
    ArrowLeft,
    LogOut,
    Send,
    UserX,
    CheckCheck,
    X,
    XOctagon,
} from "lucide-react";
import { format } from "date-fns";

export default function AdminDashboard() {
    const navigate = useNavigate();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [waitlistUsers, setWaitlistUsers] = useState<WaitlistUser[]>([]);
    const [allUsers, setAllUsers] = useState<AdminUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [waitlistLoading, setWaitlistLoading] = useState(false);
    const [usersLoading, setUsersLoading] = useState(false);

    // Waitlist global settings
    const [waitlistEnabled, setWaitlistEnabled] = useState(true);
    const [waitlistSettingsLoading, setWaitlistSettingsLoading] =
        useState(false);

    // Pagination
    const [waitlistPage, setWaitlistPage] = useState(1);
    const [waitlistTotalPages, setWaitlistTotalPages] = useState(1);
    const [waitlistTotal, setWaitlistTotal] = useState(0);
    const [usersPage, setUsersPage] = useState(1);
    const [usersTotalPages, setUsersTotalPages] = useState(1);
    const [usersTotal, setUsersTotal] = useState(0);

    // Filters
    const [waitlistFilter, setWaitlistFilter] = useState<
        "pending" | "approved" | "all"
    >("pending");
    const [waitlistSearch, setWaitlistSearch] = useState("");
    const [usersSearch, setUsersSearch] = useState("");

    // Actions
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [sendEmail, setSendEmail] = useState(true);

    // Dialog
    const [selectedUser, setSelectedUser] = useState<WaitlistUser | null>(null);
    const [showApproveDialog, setShowApproveDialog] = useState(false);

    // Bulk selection
    const [selectedWaitlistIds, setSelectedWaitlistIds] = useState<Set<string>>(
        new Set()
    );
    const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(
        new Set()
    );
    const [bulkActionLoading, setBulkActionLoading] = useState(false);

    // Email composer
    const [showEmailDialog, setShowEmailDialog] = useState(false);
    const [emailRecipients, setEmailRecipients] = useState<string[]>([]);
    const [emailSubject, setEmailSubject] = useState("");
    const [emailMessage, setEmailMessage] = useState("");
    const [emailSending, setEmailSending] = useState(false);
    const [allUserEmails, setAllUserEmails] = useState<
        Array<{ email: string; name: string }>
    >([]);

    const { toast } = useToast();

    // Load dashboard stats
    const loadStats = useCallback(async () => {
        try {
            const data = await adminApi.getStats();
            setStats(data);
        } catch (error) {
            console.error("Failed to load stats:", error);
            toast({
                title: "Error",
                description: "Failed to load dashboard statistics",
                variant: "destructive",
            });
        }
    }, [toast]);

    // Load waitlist
    const loadWaitlist = useCallback(async () => {
        setWaitlistLoading(true);
        try {
            const data = await adminApi.getWaitlist({
                page: waitlistPage,
                page_size: 10,
                status_filter: waitlistFilter,
                search: waitlistSearch || undefined,
            });
            setWaitlistUsers(data.items);
            setWaitlistTotalPages(data.total_pages);
            setWaitlistTotal(data.total);
        } catch (error) {
            console.error("Failed to load waitlist:", error);
        } finally {
            setWaitlistLoading(false);
        }
    }, [waitlistPage, waitlistFilter, waitlistSearch]);

    // Load users
    const loadUsers = useCallback(async () => {
        setUsersLoading(true);
        try {
            const data = await adminApi.getUsers({
                page: usersPage,
                page_size: 10,
                search: usersSearch || undefined,
            });
            setAllUsers(data.items);
            setUsersTotalPages(data.total_pages);
            setUsersTotal(data.total);
        } catch (error) {
            console.error("Failed to load users:", error);
        } finally {
            setUsersLoading(false);
        }
    }, [usersPage, usersSearch]);

    // Load waitlist settings
    const loadWaitlistSettings = useCallback(async () => {
        try {
            const data = await adminApi.getWaitlistSettings();
            setWaitlistEnabled(data.waitlist_enabled);
        } catch (error) {
            console.error("Failed to load waitlist settings:", error);
        }
    }, []);

    // Toggle waitlist enabled
    const handleToggleWaitlist = async (enabled: boolean) => {
        setWaitlistSettingsLoading(true);
        try {
            await adminApi.updateWaitlistSettings(enabled);
            setWaitlistEnabled(enabled);
            toast({
                title: enabled ? "Waitlist Enabled" : "Waitlist Disabled",
                description: enabled
                    ? "New users will need approval before accessing the app."
                    : "All users now have direct access to the app without approval.",
            });
        } catch (error: unknown) {
            console.error("Failed to update waitlist settings:", error);
            // Extract server-provided message when available to give better feedback
            const errAny = error as any;
            const serverMsg =
                errAny?.response?.data?.detail ||
                errAny?.response?.data?.message ||
                (errAny?.message ?? "Failed to update waitlist settings");
            toast({
                title: "Error",
                description: serverMsg,
                variant: "destructive",
            });
        } finally {
            setWaitlistSettingsLoading(false);
        }
    };

    // Initial load
    useEffect(() => {
        const init = async () => {
            setLoading(true);
            await Promise.all([loadStats(), loadWaitlistSettings()]);
            setLoading(false);
        };
        init();
    }, [loadStats, loadWaitlistSettings]);

    // Load waitlist when filters change
    useEffect(() => {
        loadWaitlist();
    }, [loadWaitlist]);

    // Load users when page/search changes
    useEffect(() => {
        loadUsers();
    }, [loadUsers]);

    // Approve user
    const handleApprove = async (user: WaitlistUser) => {
        setSelectedUser(user);
        setShowApproveDialog(true);
    };

    const confirmApprove = async () => {
        if (!selectedUser) return;

        setActionLoading(selectedUser.id);
        try {
            const result = await adminApi.approveUser(
                selectedUser.id,
                sendEmail
            );
            toast({
                title: "User Approved! 🎉",
                description: result.email_sent
                    ? `${selectedUser.email} has been approved and notified via email.`
                    : `${selectedUser.email} has been approved.`,
            });
            loadWaitlist();
            loadStats();
        } catch (error) {
            console.error("Failed to approve user:", error);
            toast({
                title: "Error",
                description: "Failed to approve user",
                variant: "destructive",
            });
        } finally {
            setActionLoading(null);
            setShowApproveDialog(false);
            setSelectedUser(null);
        }
    };

    // Reject user
    const handleReject = async (user: WaitlistUser) => {
        setActionLoading(user.id);
        try {
            await adminApi.rejectUser(user.id);
            toast({
                title: "Access Revoked",
                description: `${user.email}'s access has been revoked.`,
            });
            loadWaitlist();
            loadStats();
        } catch (error) {
            console.error("Failed to reject user:", error);
            toast({
                title: "Error",
                description: "Failed to revoke access",
                variant: "destructive",
            });
        } finally {
            setActionLoading(null);
        }
    };

    // Toggle admin
    const handleToggleAdmin = async (user: AdminUser) => {
        setActionLoading(user.id);
        try {
            if (user.is_admin) {
                await adminApi.removeAdmin(user.id);
                toast({
                    title: "Admin Removed",
                    description: `${user.email} is no longer an admin.`,
                });
            } else {
                await adminApi.makeAdmin(user.id);
                toast({
                    title: "Admin Added",
                    description: `${user.email} is now an admin.`,
                });
            }
            loadUsers();
        } catch (error: unknown) {
            console.error("Failed to toggle admin:", error);
            const message =
                error instanceof Error
                    ? error.message
                    : "Failed to update admin status";
            toast({
                title: "Error",
                description: message,
                variant: "destructive",
            });
        } finally {
            setActionLoading(null);
        }
    };

    // Toggle user access (approve/revoke)
    const handleToggleUserAccess = async (user: AdminUser) => {
        setActionLoading(user.id);
        try {
            const result = await adminApi.toggleUserAccess(user.id);
            toast({
                title: user.is_waitlist_approved
                    ? "Access Revoked"
                    : "Access Granted",
                description: result.message,
            });
            loadUsers();
            loadStats();
        } catch (error: unknown) {
            console.error("Failed to toggle user access:", error);
            const message =
                error instanceof Error
                    ? error.message
                    : "Failed to update user access";
            toast({
                title: "Error",
                description: message,
                variant: "destructive",
            });
        } finally {
            setActionLoading(null);
        }
    };

    // Bulk selection handlers
    const toggleWaitlistSelection = (userId: string) => {
        const newSelection = new Set(selectedWaitlistIds);
        if (newSelection.has(userId)) {
            newSelection.delete(userId);
        } else {
            newSelection.add(userId);
        }
        setSelectedWaitlistIds(newSelection);
    };

    const selectAllWaitlist = () => {
        if (selectedWaitlistIds.size === waitlistUsers.length) {
            setSelectedWaitlistIds(new Set());
        } else {
            setSelectedWaitlistIds(new Set(waitlistUsers.map((u) => u.id)));
        }
    };

    const selectAllUsers = () => {
        if (selectedUserIds.size === allUsers.length) {
            setSelectedUserIds(new Set());
        } else {
            setSelectedUserIds(new Set(allUsers.map((u) => u.id)));
        }
    };

    // Bulk approve
    const handleBulkApprove = async () => {
        if (selectedWaitlistIds.size === 0) return;
        setBulkActionLoading(true);
        try {
            const result = await adminApi.bulkApproveUsers(
                Array.from(selectedWaitlistIds),
                sendEmail
            );
            toast({
                title: "Bulk Approve Complete 🎉",
                description: result.message,
            });
            setSelectedWaitlistIds(new Set());
            loadWaitlist();
            loadStats();
        } catch (error) {
            console.error("Bulk approve failed:", error);
            toast({
                title: "Error",
                description: "Failed to bulk approve users",
                variant: "destructive",
            });
        } finally {
            setBulkActionLoading(false);
        }
    };

    // Bulk reject
    const handleBulkReject = async () => {
        if (selectedWaitlistIds.size === 0) return;
        setBulkActionLoading(true);
        try {
            const result = await adminApi.bulkRejectUsers(
                Array.from(selectedWaitlistIds)
            );
            toast({
                title: "Bulk Reject Complete",
                description: result.message,
            });
            setSelectedWaitlistIds(new Set());
            loadWaitlist();
            loadStats();
        } catch (error) {
            console.error("Bulk reject failed:", error);
            toast({
                title: "Error",
                description: "Failed to bulk reject users",
                variant: "destructive",
            });
        } finally {
            setBulkActionLoading(false);
        }
    };

    // Email composer
    const openEmailComposer = (emails?: string[]) => {
        if (emails && emails.length > 0) {
            setEmailRecipients(emails);
        } else {
            setEmailRecipients([]);
        }
        setEmailSubject("");
        setEmailMessage("");
        setShowEmailDialog(true);
    };

    const loadUserEmails = async () => {
        try {
            const emails = await adminApi.getUserEmails();
            setAllUserEmails(emails);
        } catch (error) {
            console.error("Failed to load user emails:", error);
        }
    };

    const handleSendEmail = async () => {
        if (
            emailRecipients.length === 0 ||
            !emailSubject.trim() ||
            !emailMessage.trim()
        ) {
            toast({
                title: "Missing Fields",
                description: "Please fill in recipients, subject, and message",
                variant: "destructive",
            });
            return;
        }
        setEmailSending(true);
        try {
            const result = await adminApi.sendEmail(
                emailRecipients,
                emailSubject,
                emailMessage
            );
            toast({
                title: "Emails Sent! 📧",
                description: `Successfully sent to ${
                    result.success_count
                } recipients${
                    result.failed.length > 0
                        ? `, ${result.failed.length} failed`
                        : ""
                }`,
            });
            setShowEmailDialog(false);
            setEmailRecipients([]);
            setEmailSubject("");
            setEmailMessage("");
        } catch (error) {
            console.error("Failed to send emails:", error);
            toast({
                title: "Error",
                description: "Failed to send emails",
                variant: "destructive",
            });
        } finally {
            setEmailSending(false);
        }
    };

    const removeEmailRecipient = (email: string) => {
        setEmailRecipients((prev) => prev.filter((e) => e !== email));
    };

    const addEmailRecipient = (email: string) => {
        if (email && !emailRecipients.includes(email)) {
            setEmailRecipients((prev) => [...prev, email]);
        }
    };

    // Email selected waitlist users
    const emailSelectedUsers = () => {
        const emails = waitlistUsers
            .filter((u) => selectedWaitlistIds.has(u.id))
            .map((u) => u.email);
        openEmailComposer(emails);
    };

    // Refresh all data
    const handleRefresh = async () => {
        setLoading(true);
        await Promise.all([
            loadStats(),
            loadWaitlist(),
            loadUsers(),
            loadUserEmails(),
        ]);
        setLoading(false);
        toast({
            title: "Refreshed",
            description: "Dashboard data has been updated.",
        });
    };

    const getInitials = (name: string | null, email: string) => {
        if (name) {
            return name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()
                .slice(0, 2);
        }
        return email.slice(0, 2).toUpperCase();
    };

    const formatDate = (dateString: string) => {
        return format(new Date(dateString), "MMM d, yyyy");
    };

    const formatDateTime = (dateString: string) => {
        return format(new Date(dateString), "MMM d, yyyy h:mm a");
    };

    const handleLogout = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        navigate("/");
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    <p className="text-muted-foreground">
                        Loading admin dashboard...
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            <div className="overflow-auto">
                <div className="p-3 sm:p-6 max-w-7xl mx-auto space-y-4 sm:space-y-6">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
                    >
                        <div className="flex items-center gap-3 sm:gap-4">
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={() => navigate("/chat")}
                                className="shrink-0"
                            >
                                <ArrowLeft className="w-4 h-4" />
                            </Button>
                            <div className="min-w-0">
                                <h1 className="text-xl sm:text-3xl font-bold flex items-center gap-2 sm:gap-3">
                                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-primary to-teal-600 flex items-center justify-center shrink-0">
                                        <Shield className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                                    </div>
                                    <span className="truncate">
                                        Admin Dashboard
                                    </span>
                                </h1>
                                <p className="text-muted-foreground mt-1 text-xs sm:text-sm hidden sm:block">
                                    Manage users, waitlist approvals, and view
                                    system statistics
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 self-end sm:self-auto">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleRefresh}
                                disabled={loading}
                                className="sm:size-default"
                            >
                                <RefreshCw
                                    className={`w-4 h-4 sm:mr-2 ${
                                        loading ? "animate-spin" : ""
                                    }`}
                                />
                                <span className="hidden sm:inline">
                                    Refresh
                                </span>
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleLogout}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50 sm:size-default"
                            >
                                <LogOut className="w-4 h-4 sm:mr-2" />
                                <span className="hidden sm:inline">Logout</span>
                            </Button>
                        </div>
                    </motion.div>

                    {/* Waitlist Toggle Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.05 }}
                    >
                        <Card
                            className={`border-2 ${
                                waitlistEnabled
                                    ? "border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/20"
                                    : "border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/20"
                            }`}
                        >
                            <CardContent className="py-3 sm:py-4">
                                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
                                    <div className="flex items-center gap-3 sm:gap-4">
                                        <div
                                            className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center shrink-0 ${
                                                waitlistEnabled
                                                    ? "bg-amber-100 dark:bg-amber-900/50"
                                                    : "bg-green-100 dark:bg-green-900/50"
                                            }`}
                                        >
                                            {waitlistEnabled ? (
                                                <Clock
                                                    className={`w-5 h-5 sm:w-6 sm:h-6 ${
                                                        waitlistEnabled
                                                            ? "text-amber-600 dark:text-amber-400"
                                                            : "text-green-600 dark:text-green-400"
                                                    }`}
                                                />
                                            ) : (
                                                <UserCheck className="w-5 h-5 sm:w-6 sm:h-6 text-green-600 dark:text-green-400" />
                                            )}
                                        </div>
                                        <div className="min-w-0">
                                            <h3 className="font-semibold text-base sm:text-lg">
                                                Waitlist Requirement
                                            </h3>
                                            <p className="text-xs sm:text-sm text-muted-foreground">
                                                {waitlistEnabled
                                                    ? "Users must be approved before accessing the app"
                                                    : "All users have direct access without approval"}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 self-end sm:self-auto">
                                        <span
                                            className={`text-xs sm:text-sm font-medium ${
                                                waitlistEnabled
                                                    ? "text-amber-600"
                                                    : "text-green-600"
                                            }`}
                                        >
                                            {waitlistEnabled
                                                ? "Enabled"
                                                : "Disabled"}
                                        </span>
                                        <Switch
                                            checked={waitlistEnabled}
                                            onCheckedChange={
                                                handleToggleWaitlist
                                            }
                                            disabled={waitlistSettingsLoading}
                                        />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Stats Cards */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4"
                    >
                        {/* Total Users */}
                        <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-blue-200 dark:border-blue-800">
                            <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-xs sm:text-sm text-muted-foreground">
                                            Total Users
                                        </p>
                                        <p className="text-xl sm:text-3xl font-bold text-blue-600 dark:text-blue-400">
                                            {stats?.total_users || 0}
                                        </p>
                                    </div>
                                    <div className="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
                                        <Users className="w-4 h-4 sm:w-6 sm:h-6 text-blue-600 dark:text-blue-400" />
                                    </div>
                                </div>
                                <div className="mt-2 sm:mt-3 flex items-center gap-1 sm:gap-2 text-[10px] sm:text-xs text-muted-foreground">
                                    <ArrowUpRight className="w-3 h-3 text-green-500" />
                                    <span className="text-green-600">
                                        +{stats?.users_today || 0} today
                                    </span>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Approved Users */}
                        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-800">
                            <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-xs sm:text-sm text-muted-foreground">
                                            Approved
                                        </p>
                                        <p className="text-xl sm:text-3xl font-bold text-green-600 dark:text-green-400">
                                            {stats?.approved_users || 0}
                                        </p>
                                    </div>
                                    <div className="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-green-100 dark:bg-green-900/50 flex items-center justify-center">
                                        <UserCheck className="w-4 h-4 sm:w-6 sm:h-6 text-green-600 dark:text-green-400" />
                                    </div>
                                </div>
                                <div className="mt-2 sm:mt-3 text-[10px] sm:text-xs text-muted-foreground">
                                    Active users
                                </div>
                            </CardContent>
                        </Card>

                        {/* Pending Waitlist */}
                        <Card className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 border-amber-200 dark:border-amber-800">
                            <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-xs sm:text-sm text-muted-foreground">
                                            Pending
                                        </p>
                                        <p className="text-xl sm:text-3xl font-bold text-amber-600 dark:text-amber-400">
                                            {stats?.pending_waitlist || 0}
                                        </p>
                                    </div>
                                    <div className="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-amber-100 dark:bg-amber-900/50 flex items-center justify-center">
                                        <Clock className="w-4 h-4 sm:w-6 sm:h-6 text-amber-600 dark:text-amber-400" />
                                    </div>
                                </div>
                                <div className="mt-2 sm:mt-3 text-[10px] sm:text-xs text-muted-foreground">
                                    Awaiting approval
                                </div>
                            </CardContent>
                        </Card>

                        {/* Messages */}
                        <Card className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20 border-purple-200 dark:border-purple-800">
                            <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-xs sm:text-sm text-muted-foreground">
                                            Messages
                                        </p>
                                        <p className="text-xl sm:text-3xl font-bold text-purple-600 dark:text-purple-400">
                                            {stats?.total_messages || 0}
                                        </p>
                                    </div>
                                    <div className="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center">
                                        <MessagesSquare className="w-4 h-4 sm:w-6 sm:h-6 text-purple-600 dark:text-purple-400" />
                                    </div>
                                </div>
                                <div className="mt-2 sm:mt-3 flex items-center gap-1 sm:gap-2 text-[10px] sm:text-xs text-muted-foreground">
                                    <MessageSquare className="w-3 h-3" />
                                    <span>
                                        {stats?.total_conversations || 0}{" "}
                                        <span className="hidden sm:inline">
                                            conversations
                                        </span>
                                        <span className="sm:hidden">chats</span>
                                    </span>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Secondary Stats */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-4"
                    >
                        <Card>
                            <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
                                <div className="flex items-center gap-3 sm:gap-4">
                                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                        <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-xs sm:text-sm text-muted-foreground">
                                            Today
                                        </p>
                                        <p className="text-lg sm:text-2xl font-semibold">
                                            {stats?.users_today || 0}{" "}
                                            <span className="text-sm sm:text-base font-normal">
                                                new
                                            </span>
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
                                <div className="flex items-center gap-3 sm:gap-4">
                                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                        <CalendarDays className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-xs sm:text-sm text-muted-foreground">
                                            This Week
                                        </p>
                                        <p className="text-lg sm:text-2xl font-semibold">
                                            {stats?.users_this_week || 0}{" "}
                                            <span className="text-sm sm:text-base font-normal">
                                                new
                                            </span>
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardContent className="pt-4 sm:pt-6 px-3 sm:px-6">
                                <div className="flex items-center gap-3 sm:gap-4">
                                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                        <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-xs sm:text-sm text-muted-foreground">
                                            This Month
                                        </p>
                                        <p className="text-lg sm:text-2xl font-semibold">
                                            {stats?.users_this_month || 0}{" "}
                                            <span className="text-sm sm:text-base font-normal">
                                                new
                                            </span>
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Tabs for Waitlist and Users */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        <Tabs
                            defaultValue="waitlist"
                            className="space-y-3 sm:space-y-4"
                        >
                            <TabsList className="grid w-full max-w-md grid-cols-2">
                                <TabsTrigger
                                    value="waitlist"
                                    className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm"
                                >
                                    <Clock className="w-3 h-3 sm:w-4 sm:h-4" />
                                    <span>Waitlist</span>
                                    {stats?.pending_waitlist ? (
                                        <Badge
                                            variant="secondary"
                                            className="ml-1 text-[10px] sm:text-xs px-1 sm:px-2"
                                        >
                                            {stats.pending_waitlist}
                                        </Badge>
                                    ) : null}
                                </TabsTrigger>
                                <TabsTrigger
                                    value="users"
                                    className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm"
                                >
                                    <Users className="w-3 h-3 sm:w-4 sm:h-4" />
                                    <span>All Users</span>
                                </TabsTrigger>
                            </TabsList>

                            {/* Waitlist Tab */}
                            <TabsContent
                                value="waitlist"
                                className="space-y-3 sm:space-y-4"
                            >
                                <Card>
                                    <CardHeader className="p-3 sm:p-6">
                                        <div className="flex flex-col gap-3 sm:gap-4">
                                            <div>
                                                <CardTitle className="text-base sm:text-lg">
                                                    Waitlist Management
                                                </CardTitle>
                                                <CardDescription className="text-xs sm:text-sm">
                                                    Approve or reject users
                                                    waiting for access
                                                </CardDescription>
                                            </div>
                                            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
                                                <div className="relative flex-1 sm:flex-none">
                                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                                    <Input
                                                        placeholder="Search by email..."
                                                        value={waitlistSearch}
                                                        onChange={(e) => {
                                                            setWaitlistSearch(
                                                                e.target.value
                                                            );
                                                            setWaitlistPage(1);
                                                        }}
                                                        className="pl-9 w-full sm:w-[200px]"
                                                    />
                                                </div>
                                                <Select
                                                    value={waitlistFilter}
                                                    onValueChange={(
                                                        value:
                                                            | "pending"
                                                            | "approved"
                                                            | "all"
                                                    ) => {
                                                        setWaitlistFilter(
                                                            value
                                                        );
                                                        setWaitlistPage(1);
                                                    }}
                                                >
                                                    <SelectTrigger className="w-[130px]">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="pending">
                                                            Pending
                                                        </SelectItem>
                                                        <SelectItem value="approved">
                                                            Approved
                                                        </SelectItem>
                                                        <SelectItem value="all">
                                                            All
                                                        </SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            {/* Bulk Action Buttons */}
                                            {selectedWaitlistIds.size > 0 && (
                                                <div className="flex flex-wrap items-center gap-2 pt-2 border-t">
                                                    <span className="text-xs text-muted-foreground">
                                                        {
                                                            selectedWaitlistIds.size
                                                        }{" "}
                                                        selected
                                                    </span>
                                                    <Button
                                                        size="sm"
                                                        className="bg-green-600 hover:bg-green-700 text-xs h-8"
                                                        onClick={
                                                            handleBulkApprove
                                                        }
                                                        disabled={
                                                            bulkActionLoading
                                                        }
                                                    >
                                                        {bulkActionLoading ? (
                                                            <Loader2 className="w-3 h-3 animate-spin mr-1" />
                                                        ) : (
                                                            <CheckCheck className="w-3 h-3 mr-1" />
                                                        )}
                                                        Approve Selected
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        className="text-red-600 hover:text-red-700 hover:bg-red-50 text-xs h-8"
                                                        onClick={
                                                            handleBulkReject
                                                        }
                                                        disabled={
                                                            bulkActionLoading
                                                        }
                                                    >
                                                        {bulkActionLoading ? (
                                                            <Loader2 className="w-3 h-3 animate-spin mr-1" />
                                                        ) : (
                                                            <XOctagon className="w-3 h-3 mr-1" />
                                                        )}
                                                        Reject Selected
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        className="text-xs h-8"
                                                        onClick={() => {
                                                            const selectedEmails =
                                                                waitlistUsers
                                                                    .filter(
                                                                        (u) =>
                                                                            selectedWaitlistIds.has(
                                                                                u.id
                                                                            )
                                                                    )
                                                                    .map(
                                                                        (u) =>
                                                                            u.email
                                                                    );
                                                            openEmailComposer(
                                                                selectedEmails
                                                            );
                                                        }}
                                                    >
                                                        <Send className="w-3 h-3 mr-1" />
                                                        Email Selected
                                                    </Button>
                                                </div>
                                            )}
                                        </div>
                                    </CardHeader>
                                    <CardContent className="p-3 sm:p-6">
                                        {waitlistLoading ? (
                                            <div className="flex items-center justify-center py-8">
                                                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                                            </div>
                                        ) : waitlistUsers.length === 0 ? (
                                            <div className="text-center py-8 text-muted-foreground">
                                                <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                                <p>No waitlist entries found</p>
                                            </div>
                                        ) : (
                                            <>
                                                {/* Mobile Card View */}
                                                <div className="space-y-3 md:hidden">
                                                    {waitlistUsers.map(
                                                        (user) => (
                                                            <div
                                                                key={user.id}
                                                                className="border rounded-lg p-3 space-y-3"
                                                            >
                                                                <div className="flex items-start justify-between gap-2">
                                                                    <div className="flex items-center gap-2 min-w-0">
                                                                        <Checkbox
                                                                            checked={selectedWaitlistIds.has(
                                                                                user.id
                                                                            )}
                                                                            onCheckedChange={() => {
                                                                                const newSet =
                                                                                    new Set(
                                                                                        selectedWaitlistIds
                                                                                    );
                                                                                if (
                                                                                    newSet.has(
                                                                                        user.id
                                                                                    )
                                                                                ) {
                                                                                    newSet.delete(
                                                                                        user.id
                                                                                    );
                                                                                } else {
                                                                                    newSet.add(
                                                                                        user.id
                                                                                    );
                                                                                }
                                                                                setSelectedWaitlistIds(
                                                                                    newSet
                                                                                );
                                                                            }}
                                                                            className="shrink-0"
                                                                        />
                                                                        <Avatar className="h-8 w-8 shrink-0">
                                                                            <AvatarImage
                                                                                src={
                                                                                    user.avatar_url ||
                                                                                    undefined
                                                                                }
                                                                            />
                                                                            <AvatarFallback className="bg-primary/10 text-primary text-xs">
                                                                                {getInitials(
                                                                                    user.name,
                                                                                    user.email
                                                                                )}
                                                                            </AvatarFallback>
                                                                        </Avatar>
                                                                        <div className="min-w-0">
                                                                            <p className="font-medium text-sm truncate">
                                                                                {user.name ||
                                                                                    "No name"}
                                                                            </p>
                                                                            <p className="text-xs text-muted-foreground truncate">
                                                                                {
                                                                                    user.email
                                                                                }
                                                                            </p>
                                                                        </div>
                                                                    </div>
                                                                    {user.is_approved ? (
                                                                        <Badge className="bg-green-100 text-green-700 hover:bg-green-100 text-[10px] shrink-0">
                                                                            <CheckCircle2 className="w-3 h-3 mr-1" />
                                                                            Approved
                                                                        </Badge>
                                                                    ) : (
                                                                        <Badge
                                                                            variant="secondary"
                                                                            className="bg-amber-100 text-amber-700 hover:bg-amber-100 text-[10px] shrink-0"
                                                                        >
                                                                            <Clock className="w-3 h-3 mr-1" />
                                                                            Pending
                                                                        </Badge>
                                                                    )}
                                                                </div>
                                                                <div className="text-xs text-muted-foreground space-y-1">
                                                                    {user.business_type && (
                                                                        <p>
                                                                            <span className="font-medium">
                                                                                Business:
                                                                            </span>{" "}
                                                                            {
                                                                                user.business_type
                                                                            }
                                                                        </p>
                                                                    )}
                                                                    {user.use_case && (
                                                                        <p className="truncate">
                                                                            <span className="font-medium">
                                                                                Use
                                                                                case:
                                                                            </span>{" "}
                                                                            {
                                                                                user.use_case
                                                                            }
                                                                        </p>
                                                                    )}
                                                                    <p>
                                                                        <span className="font-medium">
                                                                            Submitted:
                                                                        </span>{" "}
                                                                        {formatDate(
                                                                            user.submitted_at
                                                                        )}
                                                                    </p>
                                                                </div>
                                                                <div className="pt-2 border-t">
                                                                    {user.is_approved ? (
                                                                        <Button
                                                                            size="sm"
                                                                            variant="outline"
                                                                            className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
                                                                            onClick={() =>
                                                                                handleReject(
                                                                                    user
                                                                                )
                                                                            }
                                                                            disabled={
                                                                                actionLoading ===
                                                                                user.id
                                                                            }
                                                                        >
                                                                            {actionLoading ===
                                                                            user.id ? (
                                                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                                            ) : (
                                                                                <>
                                                                                    <XCircle className="w-4 h-4 mr-1" />
                                                                                    Revoke
                                                                                    Access
                                                                                </>
                                                                            )}
                                                                        </Button>
                                                                    ) : (
                                                                        <Button
                                                                            size="sm"
                                                                            className="w-full bg-green-600 hover:bg-green-700"
                                                                            onClick={() =>
                                                                                handleApprove(
                                                                                    user
                                                                                )
                                                                            }
                                                                            disabled={
                                                                                actionLoading ===
                                                                                user.id
                                                                            }
                                                                        >
                                                                            {actionLoading ===
                                                                            user.id ? (
                                                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                                            ) : (
                                                                                <>
                                                                                    <CheckCircle2 className="w-4 h-4 mr-1" />
                                                                                    Approve
                                                                                </>
                                                                            )}
                                                                        </Button>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        )
                                                    )}
                                                </div>

                                                {/* Desktop Table View */}
                                                <div className="rounded-md border hidden md:block">
                                                    <Table>
                                                        <TableHeader>
                                                            <TableRow>
                                                                <TableHead className="w-[40px]">
                                                                    <Checkbox
                                                                        checked={
                                                                            selectedWaitlistIds.size ===
                                                                                waitlistUsers.length &&
                                                                            waitlistUsers.length >
                                                                                0
                                                                        }
                                                                        onCheckedChange={() =>
                                                                            selectAllWaitlist()
                                                                        }
                                                                    />
                                                                </TableHead>
                                                                <TableHead>
                                                                    User
                                                                </TableHead>
                                                                <TableHead>
                                                                    Details
                                                                </TableHead>
                                                                <TableHead>
                                                                    Submitted
                                                                </TableHead>
                                                                <TableHead>
                                                                    Status
                                                                </TableHead>
                                                                <TableHead className="text-right">
                                                                    Actions
                                                                </TableHead>
                                                            </TableRow>
                                                        </TableHeader>
                                                        <TableBody>
                                                            {waitlistUsers.map(
                                                                (user) => (
                                                                    <TableRow
                                                                        key={
                                                                            user.id
                                                                        }
                                                                    >
                                                                        <TableCell>
                                                                            <Checkbox
                                                                                checked={selectedWaitlistIds.has(
                                                                                    user.id
                                                                                )}
                                                                                onCheckedChange={() => {
                                                                                    const newSet =
                                                                                        new Set(
                                                                                            selectedWaitlistIds
                                                                                        );
                                                                                    if (
                                                                                        newSet.has(
                                                                                            user.id
                                                                                        )
                                                                                    ) {
                                                                                        newSet.delete(
                                                                                            user.id
                                                                                        );
                                                                                    } else {
                                                                                        newSet.add(
                                                                                            user.id
                                                                                        );
                                                                                    }
                                                                                    setSelectedWaitlistIds(
                                                                                        newSet
                                                                                    );
                                                                                }}
                                                                            />
                                                                        </TableCell>
                                                                        <TableCell>
                                                                            <div className="flex items-center gap-3">
                                                                                <Avatar className="h-9 w-9">
                                                                                    <AvatarImage
                                                                                        src={
                                                                                            user.avatar_url ||
                                                                                            undefined
                                                                                        }
                                                                                    />
                                                                                    <AvatarFallback className="bg-primary/10 text-primary text-sm">
                                                                                        {getInitials(
                                                                                            user.name,
                                                                                            user.email
                                                                                        )}
                                                                                    </AvatarFallback>
                                                                                </Avatar>
                                                                                <div>
                                                                                    <p className="font-medium">
                                                                                        {user.name ||
                                                                                            "No name"}
                                                                                    </p>
                                                                                    <p className="text-sm text-muted-foreground">
                                                                                        {
                                                                                            user.email
                                                                                        }
                                                                                    </p>
                                                                                </div>
                                                                            </div>
                                                                        </TableCell>
                                                                        <TableCell>
                                                                            <div className="space-y-1 max-w-xs">
                                                                                {user.business_type && (
                                                                                    <p className="text-sm">
                                                                                        <span className="text-muted-foreground">
                                                                                            Business:
                                                                                        </span>{" "}
                                                                                        {
                                                                                            user.business_type
                                                                                        }
                                                                                    </p>
                                                                                )}
                                                                                {user.use_case && (
                                                                                    <p className="text-sm truncate">
                                                                                        <span className="text-muted-foreground">
                                                                                            Use
                                                                                            case:
                                                                                        </span>{" "}
                                                                                        {
                                                                                            user.use_case
                                                                                        }
                                                                                    </p>
                                                                                )}
                                                                                {user.oauth_provider && (
                                                                                    <Badge
                                                                                        variant="outline"
                                                                                        className="text-xs"
                                                                                    >
                                                                                        {
                                                                                            user.oauth_provider
                                                                                        }
                                                                                    </Badge>
                                                                                )}
                                                                            </div>
                                                                        </TableCell>
                                                                        <TableCell>
                                                                            <p className="text-sm">
                                                                                {formatDate(
                                                                                    user.submitted_at
                                                                                )}
                                                                            </p>
                                                                        </TableCell>
                                                                        <TableCell>
                                                                            {user.is_approved ? (
                                                                                <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                                                                                    <CheckCircle2 className="w-3 h-3 mr-1" />
                                                                                    Approved
                                                                                </Badge>
                                                                            ) : (
                                                                                <Badge
                                                                                    variant="secondary"
                                                                                    className="bg-amber-100 text-amber-700 hover:bg-amber-100"
                                                                                >
                                                                                    <Clock className="w-3 h-3 mr-1" />
                                                                                    Pending
                                                                                </Badge>
                                                                            )}
                                                                        </TableCell>
                                                                        <TableCell className="text-right">
                                                                            <div className="flex items-center justify-end gap-2">
                                                                                {user.is_approved ? (
                                                                                    <Button
                                                                                        size="sm"
                                                                                        variant="outline"
                                                                                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                                                                        onClick={() =>
                                                                                            handleReject(
                                                                                                user
                                                                                            )
                                                                                        }
                                                                                        disabled={
                                                                                            actionLoading ===
                                                                                            user.id
                                                                                        }
                                                                                    >
                                                                                        {actionLoading ===
                                                                                        user.id ? (
                                                                                            <Loader2 className="w-4 h-4 animate-spin" />
                                                                                        ) : (
                                                                                            <>
                                                                                                <XCircle className="w-4 h-4 mr-1" />
                                                                                                Revoke
                                                                                            </>
                                                                                        )}
                                                                                    </Button>
                                                                                ) : (
                                                                                    <Button
                                                                                        size="sm"
                                                                                        className="bg-green-600 hover:bg-green-700"
                                                                                        onClick={() =>
                                                                                            handleApprove(
                                                                                                user
                                                                                            )
                                                                                        }
                                                                                        disabled={
                                                                                            actionLoading ===
                                                                                            user.id
                                                                                        }
                                                                                    >
                                                                                        {actionLoading ===
                                                                                        user.id ? (
                                                                                            <Loader2 className="w-4 h-4 animate-spin" />
                                                                                        ) : (
                                                                                            <>
                                                                                                <CheckCircle2 className="w-4 h-4 mr-1" />
                                                                                                Approve
                                                                                            </>
                                                                                        )}
                                                                                    </Button>
                                                                                )}
                                                                            </div>
                                                                        </TableCell>
                                                                    </TableRow>
                                                                )
                                                            )}
                                                        </TableBody>
                                                    </Table>
                                                </div>

                                                {/* Pagination */}
                                                <div className="flex flex-col sm:flex-row items-center justify-between gap-2 mt-4">
                                                    <p className="text-xs sm:text-sm text-muted-foreground order-2 sm:order-1">
                                                        Showing{" "}
                                                        {waitlistUsers.length}{" "}
                                                        of {waitlistTotal}{" "}
                                                        entries
                                                    </p>
                                                    <div className="flex items-center gap-2 order-1 sm:order-2">
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() =>
                                                                setWaitlistPage(
                                                                    (p) =>
                                                                        Math.max(
                                                                            1,
                                                                            p -
                                                                                1
                                                                        )
                                                                )
                                                            }
                                                            disabled={
                                                                waitlistPage ===
                                                                1
                                                            }
                                                        >
                                                            <ChevronLeft className="w-4 h-4" />
                                                        </Button>
                                                        <span className="text-sm">
                                                            Page {waitlistPage}{" "}
                                                            of{" "}
                                                            {waitlistTotalPages}
                                                        </span>
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() =>
                                                                setWaitlistPage(
                                                                    (p) =>
                                                                        Math.min(
                                                                            waitlistTotalPages,
                                                                            p +
                                                                                1
                                                                        )
                                                                )
                                                            }
                                                            disabled={
                                                                waitlistPage ===
                                                                waitlistTotalPages
                                                            }
                                                        >
                                                            <ChevronRight className="w-4 h-4" />
                                                        </Button>
                                                    </div>
                                                </div>
                                            </>
                                        )}
                                    </CardContent>
                                </Card>
                            </TabsContent>

                            {/* Users Tab */}
                            <TabsContent
                                value="users"
                                className="space-y-3 sm:space-y-4"
                            >
                                <Card>
                                    <CardHeader className="p-3 sm:p-6">
                                        <div className="flex flex-col gap-3 sm:gap-4">
                                            <div>
                                                <CardTitle className="text-base sm:text-lg">
                                                    User Management
                                                </CardTitle>
                                                <CardDescription className="text-xs sm:text-sm">
                                                    View all users and manage
                                                    admin privileges
                                                </CardDescription>
                                            </div>
                                            <div className="relative">
                                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                                <Input
                                                    placeholder="Search users..."
                                                    value={usersSearch}
                                                    onChange={(e) => {
                                                        setUsersSearch(
                                                            e.target.value
                                                        );
                                                        setUsersPage(1);
                                                    }}
                                                    className="pl-9 w-full sm:w-[250px]"
                                                />
                                            </div>
                                            {/* Bulk Action Buttons */}
                                            {selectedUserIds.size > 0 && (
                                                <div className="flex flex-wrap items-center gap-2 pt-2 border-t">
                                                    <span className="text-xs text-muted-foreground">
                                                        {selectedUserIds.size}{" "}
                                                        selected
                                                    </span>
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        className="text-xs h-8"
                                                        onClick={() => {
                                                            const selectedEmails =
                                                                allUsers
                                                                    .filter(
                                                                        (u) =>
                                                                            selectedUserIds.has(
                                                                                u.id
                                                                            )
                                                                    )
                                                                    .map(
                                                                        (u) =>
                                                                            u.email
                                                                    );
                                                            openEmailComposer(
                                                                selectedEmails
                                                            );
                                                        }}
                                                    >
                                                        <Send className="w-3 h-3 mr-1" />
                                                        Email Selected
                                                    </Button>
                                                </div>
                                            )}
                                        </div>
                                    </CardHeader>
                                    <CardContent className="p-3 sm:p-6">
                                        {usersLoading ? (
                                            <div className="flex items-center justify-center py-8">
                                                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                                            </div>
                                        ) : allUsers.length === 0 ? (
                                            <div className="text-center py-8 text-muted-foreground">
                                                <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                                <p>No users found</p>
                                            </div>
                                        ) : (
                                            <>
                                                {/* Mobile Card View */}
                                                <div className="space-y-3 md:hidden">
                                                    {allUsers.map((user) => (
                                                        <div
                                                            key={user.id}
                                                            className="border rounded-lg p-3 space-y-3"
                                                        >
                                                            <div className="flex items-start justify-between gap-2">
                                                                <div className="flex items-center gap-2 min-w-0">
                                                                    <Checkbox
                                                                        checked={selectedUserIds.has(
                                                                            user.id
                                                                        )}
                                                                        onCheckedChange={() => {
                                                                            const newSet =
                                                                                new Set(
                                                                                    selectedUserIds
                                                                                );
                                                                            if (
                                                                                newSet.has(
                                                                                    user.id
                                                                                )
                                                                            ) {
                                                                                newSet.delete(
                                                                                    user.id
                                                                                );
                                                                            } else {
                                                                                newSet.add(
                                                                                    user.id
                                                                                );
                                                                            }
                                                                            setSelectedUserIds(
                                                                                newSet
                                                                            );
                                                                        }}
                                                                        className="shrink-0"
                                                                    />
                                                                    <Avatar className="h-8 w-8 shrink-0">
                                                                        <AvatarImage
                                                                            src={
                                                                                user.avatar_url ||
                                                                                undefined
                                                                            }
                                                                        />
                                                                        <AvatarFallback className="bg-primary/10 text-primary text-xs">
                                                                            {getInitials(
                                                                                user.name,
                                                                                user.email
                                                                            )}
                                                                        </AvatarFallback>
                                                                    </Avatar>
                                                                    <div className="min-w-0">
                                                                        <div className="flex items-center gap-1">
                                                                            <p className="font-medium text-sm truncate">
                                                                                {user.name ||
                                                                                    "No name"}
                                                                            </p>
                                                                            {user.is_admin && (
                                                                                <Badge
                                                                                    variant="secondary"
                                                                                    className="text-[10px] px-1 shrink-0"
                                                                                >
                                                                                    <Shield className="w-2 h-2 mr-0.5" />
                                                                                    Admin
                                                                                </Badge>
                                                                            )}
                                                                        </div>
                                                                        <p className="text-xs text-muted-foreground truncate">
                                                                            {
                                                                                user.email
                                                                            }
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                                                                <div>
                                                                    <span className="font-medium">
                                                                        Status:
                                                                    </span>{" "}
                                                                    {user.is_waitlist_approved ? (
                                                                        <Badge className="bg-green-100 text-green-700 text-[10px] px-1">
                                                                            Approved
                                                                        </Badge>
                                                                    ) : (
                                                                        <Badge
                                                                            variant="secondary"
                                                                            className="bg-amber-100 text-amber-700 text-[10px] px-1"
                                                                        >
                                                                            Pending
                                                                        </Badge>
                                                                    )}
                                                                </div>
                                                                <div>
                                                                    <span className="font-medium">
                                                                        Joined:
                                                                    </span>{" "}
                                                                    {formatDate(
                                                                        user.created_at
                                                                    )}
                                                                </div>
                                                                <div>
                                                                    <span className="font-medium">
                                                                        Conversations:
                                                                    </span>{" "}
                                                                    {
                                                                        user.conversation_count
                                                                    }
                                                                </div>
                                                                <div>
                                                                    <span className="font-medium">
                                                                        Messages:
                                                                    </span>{" "}
                                                                    {
                                                                        user.message_count
                                                                    }
                                                                </div>
                                                            </div>
                                                            <div className="pt-2 border-t space-y-2">
                                                                <div className="flex items-center justify-between">
                                                                    <span className="text-xs text-muted-foreground">
                                                                        App
                                                                        Access
                                                                    </span>
                                                                    <Button
                                                                        size="sm"
                                                                        variant={
                                                                            user.is_waitlist_approved
                                                                                ? "outline"
                                                                                : "default"
                                                                        }
                                                                        className={
                                                                            user.is_waitlist_approved
                                                                                ? "text-red-600 hover:text-red-700 hover:bg-red-50 text-xs h-7"
                                                                                : "bg-green-600 hover:bg-green-700 text-xs h-7"
                                                                        }
                                                                        onClick={() =>
                                                                            handleToggleUserAccess(
                                                                                user
                                                                            )
                                                                        }
                                                                        disabled={
                                                                            actionLoading ===
                                                                            user.id
                                                                        }
                                                                    >
                                                                        {actionLoading ===
                                                                        user.id ? (
                                                                            <Loader2 className="w-3 h-3 animate-spin" />
                                                                        ) : user.is_waitlist_approved ? (
                                                                            <>
                                                                                <XCircle className="w-3 h-3 mr-1" />
                                                                                Revoke
                                                                            </>
                                                                        ) : (
                                                                            <>
                                                                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                                                                Approve
                                                                            </>
                                                                        )}
                                                                    </Button>
                                                                </div>
                                                                <div className="flex items-center justify-between">
                                                                    <span className="text-xs text-muted-foreground">
                                                                        Admin
                                                                        access
                                                                    </span>
                                                                    <Switch
                                                                        checked={
                                                                            user.is_admin
                                                                        }
                                                                        onCheckedChange={() =>
                                                                            handleToggleAdmin(
                                                                                user
                                                                            )
                                                                        }
                                                                        disabled={
                                                                            actionLoading ===
                                                                            user.id
                                                                        }
                                                                    />
                                                                </div>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>

                                                {/* Desktop Table View */}
                                                <div className="rounded-md border hidden md:block">
                                                    <Table>
                                                        <TableHeader>
                                                            <TableRow>
                                                                <TableHead className="w-[40px]">
                                                                    <Checkbox
                                                                        checked={
                                                                            selectedUserIds.size ===
                                                                                allUsers.length &&
                                                                            allUsers.length >
                                                                                0
                                                                        }
                                                                        onCheckedChange={() =>
                                                                            selectAllUsers()
                                                                        }
                                                                    />
                                                                </TableHead>
                                                                <TableHead>
                                                                    User
                                                                </TableHead>
                                                                <TableHead>
                                                                    Status
                                                                </TableHead>
                                                                <TableHead>
                                                                    Activity
                                                                </TableHead>
                                                                <TableHead>
                                                                    Joined
                                                                </TableHead>
                                                                <TableHead>
                                                                    Access
                                                                </TableHead>
                                                                <TableHead className="text-right">
                                                                    Admin
                                                                </TableHead>
                                                            </TableRow>
                                                        </TableHeader>
                                                        <TableBody>
                                                            {allUsers.map(
                                                                (user) => (
                                                                    <TableRow
                                                                        key={
                                                                            user.id
                                                                        }
                                                                    >
                                                                        <TableCell>
                                                                            <Checkbox
                                                                                checked={selectedUserIds.has(
                                                                                    user.id
                                                                                )}
                                                                                onCheckedChange={() => {
                                                                                    const newSet =
                                                                                        new Set(
                                                                                            selectedUserIds
                                                                                        );
                                                                                    if (
                                                                                        newSet.has(
                                                                                            user.id
                                                                                        )
                                                                                    ) {
                                                                                        newSet.delete(
                                                                                            user.id
                                                                                        );
                                                                                    } else {
                                                                                        newSet.add(
                                                                                            user.id
                                                                                        );
                                                                                    }
                                                                                    setSelectedUserIds(
                                                                                        newSet
                                                                                    );
                                                                                }}
                                                                            />
                                                                        </TableCell>
                                                                        <TableCell>
                                                                            <div className="flex items-center gap-3">
                                                                                <Avatar className="h-9 w-9">
                                                                                    <AvatarImage
                                                                                        src={
                                                                                            user.avatar_url ||
                                                                                            undefined
                                                                                        }
                                                                                    />
                                                                                    <AvatarFallback className="bg-primary/10 text-primary text-sm">
                                                                                        {getInitials(
                                                                                            user.name,
                                                                                            user.email
                                                                                        )}
                                                                                    </AvatarFallback>
                                                                                </Avatar>
                                                                                <div>
                                                                                    <div className="flex items-center gap-2">
                                                                                        <p className="font-medium">
                                                                                            {user.name ||
                                                                                                "No name"}
                                                                                        </p>
                                                                                        {user.is_admin && (
                                                                                            <Badge className="bg-purple-100 text-purple-700 hover:bg-purple-100">
                                                                                                <Shield className="w-3 h-3 mr-1" />
                                                                                                Admin
                                                                                            </Badge>
                                                                                        )}
                                                                                    </div>
                                                                                    <p className="text-sm text-muted-foreground">
                                                                                        {
                                                                                            user.email
                                                                                        }
                                                                                    </p>
                                                                                </div>
                                                                            </div>
                                                                        </TableCell>
                                                                        <TableCell>
                                                                            <div className="flex flex-col gap-1">
                                                                                {user.is_waitlist_approved ? (
                                                                                    <Badge className="bg-green-100 text-green-700 hover:bg-green-100 w-fit">
                                                                                        Approved
                                                                                    </Badge>
                                                                                ) : (
                                                                                    <Badge
                                                                                        variant="secondary"
                                                                                        className="w-fit"
                                                                                    >
                                                                                        Waitlisted
                                                                                    </Badge>
                                                                                )}
                                                                                {user.oauth_provider && (
                                                                                    <Badge
                                                                                        variant="outline"
                                                                                        className="text-xs w-fit"
                                                                                    >
                                                                                        {
                                                                                            user.oauth_provider
                                                                                        }
                                                                                    </Badge>
                                                                                )}
                                                                            </div>
                                                                        </TableCell>
                                                                        <TableCell>
                                                                            <div className="space-y-1 text-sm">
                                                                                <p className="flex items-center gap-1">
                                                                                    <MessageSquare className="w-3 h-3 text-muted-foreground" />
                                                                                    {
                                                                                        user.conversation_count
                                                                                    }{" "}
                                                                                    conversations
                                                                                </p>
                                                                                <p className="flex items-center gap-1">
                                                                                    <MessagesSquare className="w-3 h-3 text-muted-foreground" />
                                                                                    {
                                                                                        user.message_count
                                                                                    }{" "}
                                                                                    messages
                                                                                </p>
                                                                            </div>
                                                                        </TableCell>
                                                                        <TableCell>
                                                                            <p className="text-sm">
                                                                                {formatDate(
                                                                                    user.created_at
                                                                                )}
                                                                            </p>
                                                                        </TableCell>
                                                                        <TableCell>
                                                                            <Button
                                                                                size="sm"
                                                                                variant={
                                                                                    user.is_waitlist_approved
                                                                                        ? "outline"
                                                                                        : "default"
                                                                                }
                                                                                className={
                                                                                    user.is_waitlist_approved
                                                                                        ? "text-red-600 hover:text-red-700 hover:bg-red-50 text-xs h-7"
                                                                                        : "bg-green-600 hover:bg-green-700 text-xs h-7"
                                                                                }
                                                                                onClick={() =>
                                                                                    handleToggleUserAccess(
                                                                                        user
                                                                                    )
                                                                                }
                                                                                disabled={
                                                                                    actionLoading ===
                                                                                    user.id
                                                                                }
                                                                            >
                                                                                {actionLoading ===
                                                                                user.id ? (
                                                                                    <Loader2 className="w-3 h-3 animate-spin" />
                                                                                ) : user.is_waitlist_approved ? (
                                                                                    <>
                                                                                        <XCircle className="w-3 h-3 mr-1" />
                                                                                        Revoke
                                                                                    </>
                                                                                ) : (
                                                                                    <>
                                                                                        <CheckCircle2 className="w-3 h-3 mr-1" />
                                                                                        Approve
                                                                                    </>
                                                                                )}
                                                                            </Button>
                                                                        </TableCell>
                                                                        <TableCell className="text-right">
                                                                            <div className="flex items-center justify-end gap-2">
                                                                                <Switch
                                                                                    checked={
                                                                                        user.is_admin
                                                                                    }
                                                                                    onCheckedChange={() =>
                                                                                        handleToggleAdmin(
                                                                                            user
                                                                                        )
                                                                                    }
                                                                                    disabled={
                                                                                        actionLoading ===
                                                                                        user.id
                                                                                    }
                                                                                />
                                                                                {actionLoading ===
                                                                                    user.id && (
                                                                                    <Loader2 className="w-4 h-4 animate-spin" />
                                                                                )}
                                                                            </div>
                                                                        </TableCell>
                                                                    </TableRow>
                                                                )
                                                            )}
                                                        </TableBody>
                                                    </Table>
                                                </div>

                                                {/* Pagination */}
                                                <div className="flex flex-col sm:flex-row items-center justify-between gap-2 mt-4">
                                                    <p className="text-xs sm:text-sm text-muted-foreground order-2 sm:order-1">
                                                        Showing{" "}
                                                        {allUsers.length} of{" "}
                                                        {usersTotal} users
                                                    </p>
                                                    <div className="flex items-center gap-2 order-1 sm:order-2">
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() =>
                                                                setUsersPage(
                                                                    (p) =>
                                                                        Math.max(
                                                                            1,
                                                                            p -
                                                                                1
                                                                        )
                                                                )
                                                            }
                                                            disabled={
                                                                usersPage === 1
                                                            }
                                                        >
                                                            <ChevronLeft className="w-4 h-4" />
                                                        </Button>
                                                        <span className="text-sm">
                                                            Page {usersPage} of{" "}
                                                            {usersTotalPages}
                                                        </span>
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={() =>
                                                                setUsersPage(
                                                                    (p) =>
                                                                        Math.min(
                                                                            usersTotalPages,
                                                                            p +
                                                                                1
                                                                        )
                                                                )
                                                            }
                                                            disabled={
                                                                usersPage ===
                                                                usersTotalPages
                                                            }
                                                        >
                                                            <ChevronRight className="w-4 h-4" />
                                                        </Button>
                                                    </div>
                                                </div>
                                            </>
                                        )}
                                    </CardContent>
                                </Card>
                            </TabsContent>
                        </Tabs>
                    </motion.div>
                </div>
            </div>

            {/* Approve Dialog */}
            <Dialog
                open={showApproveDialog}
                onOpenChange={setShowApproveDialog}
            >
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-green-600" />
                            Approve User
                        </DialogTitle>
                        <DialogDescription>
                            You're about to approve{" "}
                            <strong>{selectedUser?.email}</strong> for full
                            access to Sahulat AI.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="py-4 space-y-4">
                        {selectedUser?.message && (
                            <div className="p-3 bg-muted rounded-lg">
                                <p className="text-sm font-medium mb-1">
                                    User's Message:
                                </p>
                                <p className="text-sm text-muted-foreground">
                                    {selectedUser.message}
                                </p>
                            </div>
                        )}

                        <div className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex items-center gap-3">
                                {sendEmail ? (
                                    <Mail className="w-5 h-5 text-primary" />
                                ) : (
                                    <MailX className="w-5 h-5 text-muted-foreground" />
                                )}
                                <div>
                                    <p className="font-medium">
                                        Send notification email
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                        Notify user via email that they've been
                                        approved
                                    </p>
                                </div>
                            </div>
                            <Switch
                                checked={sendEmail}
                                onCheckedChange={setSendEmail}
                            />
                        </div>
                    </div>

                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setShowApproveDialog(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            className="bg-green-600 hover:bg-green-700"
                            onClick={confirmApprove}
                            disabled={actionLoading !== null}
                        >
                            {actionLoading ? (
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : (
                                <CheckCircle2 className="w-4 h-4 mr-2" />
                            )}
                            Approve User
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Email Composer Dialog */}
            <Dialog open={showEmailDialog} onOpenChange={setShowEmailDialog}>
                <DialogContent className="sm:max-w-[600px]">
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2">
                            <Send className="w-5 h-5" />
                            Compose Email
                        </DialogTitle>
                        <DialogDescription>
                            Send a custom email to selected users
                        </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {/* Recipients */}
                        <div className="space-y-2">
                            <Label>Recipients ({emailRecipients.length})</Label>
                            <div className="flex flex-wrap gap-2 p-2 border rounded-lg min-h-[60px] max-h-[120px] overflow-y-auto bg-muted/30">
                                {emailRecipients.length === 0 ? (
                                    <span className="text-sm text-muted-foreground">
                                        No recipients selected
                                    </span>
                                ) : (
                                    emailRecipients.map((email) => (
                                        <span
                                            key={email}
                                            className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary text-xs rounded-full"
                                        >
                                            {email}
                                            <button
                                                type="button"
                                                onClick={() =>
                                                    removeEmailRecipient(email)
                                                }
                                                className="hover:text-red-500 ml-1"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Subject */}
                        <div className="space-y-2">
                            <Label htmlFor="email-subject">Subject</Label>
                            <Input
                                id="email-subject"
                                placeholder="Enter email subject..."
                                value={emailSubject}
                                onChange={(e) =>
                                    setEmailSubject(e.target.value)
                                }
                            />
                        </div>

                        {/* Message */}
                        <div className="space-y-2">
                            <Label htmlFor="email-message">Message</Label>
                            <Textarea
                                id="email-message"
                                placeholder="Write your message here..."
                                value={emailMessage}
                                onChange={(e) =>
                                    setEmailMessage(e.target.value)
                                }
                                rows={8}
                                className="resize-none"
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setShowEmailDialog(false)}
                            disabled={emailSending}
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSendEmail}
                            disabled={
                                emailSending ||
                                emailRecipients.length === 0 ||
                                !emailSubject.trim() ||
                                !emailMessage.trim()
                            }
                        >
                            {emailSending ? (
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : (
                                <Send className="w-4 h-4 mr-2" />
                            )}
                            Send Email
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
