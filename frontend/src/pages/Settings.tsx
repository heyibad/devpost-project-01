import { useState, useEffect } from "react";
import ChatSidebar from "@/components/ChatSidebar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { authApi, api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import {
    User,
    Bell,
    Shield,
    LogOut,
    Loader2,
    Key,
    Eye,
    EyeOff,
} from "lucide-react";

interface PasswordStatus {
    has_password: boolean;
    is_oauth_user: boolean;
    oauth_provider: string | null;
}

export default function Settings() {
    const [notifications, setNotifications] = useState(true);
    const { toast } = useToast();
    const navigate = useNavigate();

    // Password management state
    const [passwordStatus, setPasswordStatus] = useState<PasswordStatus | null>(
        null
    );
    const [loadingPasswordStatus, setLoadingPasswordStatus] = useState(true);
    const [showPasswordForm, setShowPasswordForm] = useState(false);
    const [savingPassword, setSavingPassword] = useState(false);

    // Password form fields
    const [currentPassword, setCurrentPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    // Fetch password status on mount
    useEffect(() => {
        const fetchPasswordStatus = async () => {
            try {
                const response = await api.get("/api/v1/auth/password-status");
                setPasswordStatus(response.data);
            } catch (error) {
                console.error("Failed to fetch password status:", error);
            } finally {
                setLoadingPasswordStatus(false);
            }
        };

        fetchPasswordStatus();
    }, []);

    const handlePasswordSubmit = async () => {
        if (!passwordStatus) return;

        // Validation
        if (passwordStatus.has_password && !currentPassword) {
            toast({
                title: "Error",
                description: "Please enter your current password",
                variant: "destructive",
            });
            return;
        }

        if (newPassword.length < 8) {
            toast({
                title: "Error",
                description: "Password must be at least 8 characters",
                variant: "destructive",
            });
            return;
        }

        if (newPassword !== confirmPassword) {
            toast({
                title: "Error",
                description: "Passwords do not match",
                variant: "destructive",
            });
            return;
        }

        setSavingPassword(true);

        try {
            if (passwordStatus.has_password) {
                // Change password
                await api.post("/api/v1/auth/change-password", {
                    old_password: currentPassword,
                    new_password: newPassword,
                });
                toast({
                    title: "Success",
                    description: "Password changed successfully",
                });
            } else {
                // Add password
                await api.post("/api/v1/auth/add-password", {
                    new_password: newPassword,
                    confirm_password: confirmPassword,
                });
                toast({
                    title: "Success",
                    description:
                        "Password added successfully. You can now login with email and password.",
                });
                // Update password status
                setPasswordStatus({ ...passwordStatus, has_password: true });
            }

            // Reset form
            setCurrentPassword("");
            setNewPassword("");
            setConfirmPassword("");
            setShowPasswordForm(false);
        } catch (error: unknown) {
            let errorMessage = "Failed to update password";
            if (error && typeof error === "object" && "response" in error) {
                const axiosError = error as {
                    response?: { data?: { detail?: string } };
                };
                errorMessage =
                    axiosError.response?.data?.detail || errorMessage;
            }
            toast({
                title: "Error",
                description: errorMessage,
                variant: "destructive",
            });
        } finally {
            setSavingPassword(false);
        }
    };

    const handleLogout = async () => {
        try {
            await authApi.logout();
            toast({
                title: "Logged out",
                description: "You have been successfully logged out.",
            });
            navigate("/");
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to logout",
                variant: "destructive",
            });
        }
    };

    return (
        <div className="flex h-screen w-full">
            <ChatSidebar currentPath="/chat/settings" />

            <main className="flex-1 overflow-y-auto bg-gradient-to-b from-background to-secondary/20 p-8 pt-16 md:pt-8">
                <div className="max-w-4xl mx-auto space-y-6">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Settings</h1>
                        <p className="text-muted-foreground">
                            Manage your account preferences and configurations
                        </p>
                    </div>

                    {/* Profile Settings */}
                    <Card className="glass p-6 border-white/30">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                <User className="w-5 h-5 text-primary" />
                            </div>
                            <h2 className="text-xl font-semibold">
                                Profile Settings
                            </h2>
                        </div>

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Full Name</Label>
                                <Input
                                    id="name"
                                    placeholder="Your name"
                                    className="glass"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="your@email.com"
                                    className="glass"
                                />
                            </div>

                            <Button>Save Changes</Button>
                        </div>
                    </Card>

                    {/* Notification Settings */}
                    <Card className="glass p-6 border-white/30">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                <Bell className="w-5 h-5 text-primary" />
                            </div>
                            <h2 className="text-xl font-semibold">
                                Notifications
                            </h2>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="font-medium">
                                        Email Notifications
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                        Receive updates about your agents and
                                        transactions
                                    </p>
                                </div>
                                <Switch
                                    checked={notifications}
                                    onCheckedChange={setNotifications}
                                />
                            </div>
                        </div>
                    </Card>

                    {/* Security Settings */}
                    <Card className="glass p-6 border-white/30">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                <Shield className="w-5 h-5 text-primary" />
                            </div>
                            <h2 className="text-xl font-semibold">Security</h2>
                        </div>

                        <div className="space-y-4">
                            {loadingPasswordStatus ? (
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Loading password status...</span>
                                </div>
                            ) : (
                                <>
                                    {/* Password Status Info */}
                                    <div className="p-4 rounded-lg bg-secondary/50 border border-border/50">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Key className="w-4 h-4 text-primary" />
                                            <span className="font-medium">
                                                Password Status
                                            </span>
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                            {passwordStatus?.has_password ? (
                                                "You have a password set. You can login with email and password."
                                            ) : passwordStatus?.is_oauth_user ? (
                                                <>
                                                    You signed up with{" "}
                                                    <span className="font-medium capitalize">
                                                        {passwordStatus.oauth_provider ||
                                                            "OAuth"}
                                                    </span>
                                                    . Add a password to also
                                                    login with email and
                                                    password.
                                                </>
                                            ) : (
                                                "No password information available."
                                            )}
                                        </p>
                                    </div>

                                    {/* Password Form Toggle Button */}
                                    {!showPasswordForm && (
                                        <Button
                                            variant="outline"
                                            className="glass"
                                            onClick={() =>
                                                setShowPasswordForm(true)
                                            }
                                        >
                                            <Key className="w-4 h-4 mr-2" />
                                            {passwordStatus?.has_password
                                                ? "Change Password"
                                                : "Add Password"}
                                        </Button>
                                    )}

                                    {/* Password Form */}
                                    {showPasswordForm && (
                                        <div className="space-y-4 p-4 rounded-lg border border-border/50 bg-card/50">
                                            <h3 className="font-medium">
                                                {passwordStatus?.has_password
                                                    ? "Change Password"
                                                    : "Add Password"}
                                            </h3>

                                            {/* Current Password - only show if user has a password */}
                                            {passwordStatus?.has_password && (
                                                <div className="space-y-2">
                                                    <Label htmlFor="current-password">
                                                        Current Password
                                                    </Label>
                                                    <div className="relative">
                                                        <Input
                                                            id="current-password"
                                                            type={
                                                                showCurrentPassword
                                                                    ? "text"
                                                                    : "password"
                                                            }
                                                            value={
                                                                currentPassword
                                                            }
                                                            onChange={(e) =>
                                                                setCurrentPassword(
                                                                    e.target
                                                                        .value
                                                                )
                                                            }
                                                            placeholder="Enter current password"
                                                            className="glass pr-10"
                                                        />
                                                        <Button
                                                            type="button"
                                                            variant="ghost"
                                                            size="icon"
                                                            className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                                            onClick={() =>
                                                                setShowCurrentPassword(
                                                                    !showCurrentPassword
                                                                )
                                                            }
                                                        >
                                                            {showCurrentPassword ? (
                                                                <EyeOff className="w-4 h-4 text-muted-foreground" />
                                                            ) : (
                                                                <Eye className="w-4 h-4 text-muted-foreground" />
                                                            )}
                                                        </Button>
                                                    </div>
                                                </div>
                                            )}

                                            {/* New Password */}
                                            <div className="space-y-2">
                                                <Label htmlFor="new-password">
                                                    New Password
                                                </Label>
                                                <div className="relative">
                                                    <Input
                                                        id="new-password"
                                                        type={
                                                            showNewPassword
                                                                ? "text"
                                                                : "password"
                                                        }
                                                        value={newPassword}
                                                        onChange={(e) =>
                                                            setNewPassword(
                                                                e.target.value
                                                            )
                                                        }
                                                        placeholder="Enter new password (min 8 characters)"
                                                        className="glass pr-10"
                                                    />
                                                    <Button
                                                        type="button"
                                                        variant="ghost"
                                                        size="icon"
                                                        className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                                        onClick={() =>
                                                            setShowNewPassword(
                                                                !showNewPassword
                                                            )
                                                        }
                                                    >
                                                        {showNewPassword ? (
                                                            <EyeOff className="w-4 h-4 text-muted-foreground" />
                                                        ) : (
                                                            <Eye className="w-4 h-4 text-muted-foreground" />
                                                        )}
                                                    </Button>
                                                </div>
                                            </div>

                                            {/* Confirm Password */}
                                            <div className="space-y-2">
                                                <Label htmlFor="confirm-password">
                                                    Confirm New Password
                                                </Label>
                                                <div className="relative">
                                                    <Input
                                                        id="confirm-password"
                                                        type={
                                                            showConfirmPassword
                                                                ? "text"
                                                                : "password"
                                                        }
                                                        value={confirmPassword}
                                                        onChange={(e) =>
                                                            setConfirmPassword(
                                                                e.target.value
                                                            )
                                                        }
                                                        placeholder="Confirm new password"
                                                        className="glass pr-10"
                                                    />
                                                    <Button
                                                        type="button"
                                                        variant="ghost"
                                                        size="icon"
                                                        className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                                                        onClick={() =>
                                                            setShowConfirmPassword(
                                                                !showConfirmPassword
                                                            )
                                                        }
                                                    >
                                                        {showConfirmPassword ? (
                                                            <EyeOff className="w-4 h-4 text-muted-foreground" />
                                                        ) : (
                                                            <Eye className="w-4 h-4 text-muted-foreground" />
                                                        )}
                                                    </Button>
                                                </div>
                                            </div>

                                            {/* Form Actions */}
                                            <div className="flex gap-3 pt-2">
                                                <Button
                                                    onClick={
                                                        handlePasswordSubmit
                                                    }
                                                    disabled={savingPassword}
                                                >
                                                    {savingPassword && (
                                                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                                    )}
                                                    {passwordStatus?.has_password
                                                        ? "Update Password"
                                                        : "Set Password"}
                                                </Button>
                                                <Button
                                                    variant="outline"
                                                    onClick={() => {
                                                        setShowPasswordForm(
                                                            false
                                                        );
                                                        setCurrentPassword("");
                                                        setNewPassword("");
                                                        setConfirmPassword("");
                                                    }}
                                                    disabled={savingPassword}
                                                >
                                                    Cancel
                                                </Button>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </Card>

                    {/* Danger Zone */}
                    <Card className="glass p-6 border-red-500/30 border-2">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                                <LogOut className="w-5 h-5 text-red-500" />
                            </div>
                            <h2 className="text-xl font-semibold">Logout</h2>
                        </div>

                        <div className="space-y-2">
                            <p className="text-sm text-muted-foreground">
                                Sign out of your account on this device
                            </p>
                            <Button
                                variant="destructive"
                                onClick={handleLogout}
                            >
                                <LogOut className="w-4 h-4 mr-2" />
                                Logout
                            </Button>
                        </div>
                    </Card>
                </div>
            </main>
        </div>
    );
}
