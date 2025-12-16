import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { waitlistApi, type WaitlistStatus } from "@/lib/api";
import { useNavigate } from "react-router-dom";
import {
    Bot,
    Clock,
    CheckCircle2,
    Send,
    Loader2,
    Sparkles,
    Users,
    Zap,
    Heart,
    AlertTriangle,
    LogOut,
    RefreshCw,
} from "lucide-react";

export default function Waitlist() {
    const [status, setStatus] = useState<WaitlistStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [message, setMessage] = useState("");
    const [useCase, setUseCase] = useState("");
    const [businessType, setBusinessType] = useState("");
    const { toast } = useToast();
    const navigate = useNavigate();

    const loadStatus = async (showRefreshing = false) => {
        if (showRefreshing) setRefreshing(true);
        try {
            const data = await waitlistApi.getStatus();
            setStatus(data);

            // Pre-fill form with existing data
            if (data.message) setMessage(data.message);
            if (data.use_case) setUseCase(data.use_case);
            if (data.business_type) setBusinessType(data.business_type);

            // If approved, redirect to chat
            if (data.is_approved) {
                toast({
                    title: "You're approved! 🎉",
                    description: "Redirecting to the app...",
                });
                setTimeout(() => navigate("/chat"), 1000);
            }
        } catch (error) {
            console.error("Failed to load waitlist status:", error);
            if (!showRefreshing) {
                toast({
                    title: "Error",
                    description: "Failed to load your waitlist status",
                    variant: "destructive",
                });
            }
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        navigate("/");
    };

    const handleRefresh = () => {
        loadStatus(true);
    };

    useEffect(() => {
        loadStatus();

        // Auto-check approval status every 30 seconds
        const interval = setInterval(() => {
            loadStatus(false);
        }, 30000);

        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleSubmit = async () => {
        setSubmitting(true);
        try {
            const response = await waitlistApi.submit({
                message: message.trim() || undefined,
                use_case: useCase.trim() || undefined,
                business_type: businessType.trim() || undefined,
            });

            setStatus(response.waitlist_status);
            toast({
                title: "Success!",
                description: response.message,
            });
        } catch (error) {
            console.error("Failed to submit waitlist:", error);
            toast({
                title: "Error",
                description: "Failed to submit your request. Please try again.",
                variant: "destructive",
            });
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Navbar */}
            <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
                <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                            <Bot className="w-5 h-5 text-primary" />
                        </div>
                        <span className="font-bold text-lg tracking-tight hidden sm:inline">
                            Sahulat AI
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleRefresh}
                            disabled={refreshing}
                            className="text-muted-foreground"
                        >
                            <RefreshCw
                                className={`w-4 h-4 ${
                                    refreshing ? "animate-spin" : ""
                                } sm:mr-2`}
                            />
                            <span className="hidden sm:inline">
                                Check Status
                            </span>
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleLogout}
                            className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                        >
                            <LogOut className="w-4 h-4 sm:mr-2" />
                            <span className="hidden sm:inline">Logout</span>
                        </Button>
                    </div>
                </div>
            </header>

            <main className="flex-1 container mx-auto px-4 py-8 md:py-12 max-w-3xl">
                {/* Hero Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center mb-8 md:mb-12 space-y-4"
                >
                    <div className="inline-flex items-center justify-center p-4 rounded-full bg-primary/10 mb-4 ring-8 ring-primary/5">
                        {status?.is_on_waitlist ? (
                            <Sparkles className="w-8 h-8 text-primary" />
                        ) : (
                            <Bot className="w-8 h-8 text-primary" />
                        )}
                    </div>
                    <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
                        {status?.is_on_waitlist
                            ? "You're on the list! 🚀"
                            : "Join the Waitlist"}
                    </h1>
                    <p className="text-xl text-muted-foreground max-w-lg mx-auto leading-relaxed">
                        {status?.is_on_waitlist
                            ? "We're onboarding new businesses every day. Thank you for your patience while we prepare your workspace."
                            : "Experience the future of business automation. Complete the form below to secure your spot."}
                    </p>
                </motion.div>

                {/* Status Cards Grid */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="grid md:grid-cols-2 gap-6 mb-12"
                >
                    {/* Position Card */}
                    {status?.is_on_waitlist && !status?.is_approved && (
                        <Card className="border-primary/20 bg-primary/5 shadow-sm">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-primary uppercase tracking-wider flex items-center gap-2">
                                    <Clock className="w-4 h-4" />
                                    Your Position
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-4xl md:text-5xl font-bold text-primary">
                                        #{status.position || "—"}
                                    </span>
                                    <span className="text-muted-foreground font-medium">
                                        in queue
                                    </span>
                                </div>
                                <p className="text-sm text-muted-foreground mt-2">
                                    Moving fast! We'll email you soon.
                                </p>
                            </CardContent>
                        </Card>
                    )}

                    {/* Info Card */}
                    <Card className="shadow-sm">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                                <AlertTriangle className="w-4 h-4" />
                                Why the wait?
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-sm text-muted-foreground leading-relaxed">
                                We're a bootstrapped startup carefully scaling
                                our AI infrastructure to ensure the best
                                performance for every business.
                            </p>
                            <div className="flex items-center gap-4 mt-4 text-xs font-medium text-muted-foreground">
                                <div className="flex items-center gap-1.5">
                                    <Heart className="w-3 h-3 text-red-500" />
                                    <span>Made in Pakistan</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                    <Zap className="w-3 h-3 text-amber-500" />
                                    <span>Bootstrapped</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Form Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <Card className="shadow-md border-muted">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Users className="w-5 h-5 text-primary" />
                                {status?.is_on_waitlist
                                    ? "Update your details"
                                    : "Complete your profile to join"}
                            </CardTitle>
                            <CardDescription>
                                {status?.is_on_waitlist
                                    ? "Keep your information up to date to help us prioritize your access."
                                    : "Tell us about your business needs to secure your spot in line. We review applications daily."}
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="grid md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <Label htmlFor="businessType">
                                        Business Type
                                    </Label>
                                    <Input
                                        id="businessType"
                                        placeholder="e.g., E-commerce, Restaurant"
                                        value={businessType}
                                        onChange={(e) =>
                                            setBusinessType(e.target.value)
                                        }
                                        maxLength={200}
                                        className="bg-background"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="useCase">
                                        Primary Goal
                                    </Label>
                                    <Input
                                        id="useCase"
                                        placeholder="e.g., Automate WhatsApp orders"
                                        value={useCase}
                                        onChange={(e) =>
                                            setUseCase(e.target.value)
                                        }
                                        maxLength={500}
                                        className="bg-background"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="message">
                                    Anything else? (Optional)
                                </Label>
                                <Textarea
                                    id="message"
                                    placeholder="Share your specific requirements or questions..."
                                    value={message}
                                    onChange={(e) => setMessage(e.target.value)}
                                    rows={3}
                                    maxLength={1000}
                                    className="resize-none bg-background"
                                />
                                <p className="text-xs text-muted-foreground text-right">
                                    {message.length}/1000
                                </p>
                            </div>

                            <div className="flex justify-end">
                                <Button
                                    onClick={handleSubmit}
                                    disabled={submitting}
                                    className="w-full sm:w-auto min-w-[140px]"
                                >
                                    {submitting ? (
                                        <>
                                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                            Saving...
                                        </>
                                    ) : status?.is_on_waitlist ? (
                                        <>
                                            <CheckCircle2 className="w-4 h-4 mr-2" />
                                            Update Info
                                        </>
                                    ) : (
                                        <>
                                            <Send className="w-4 h-4 mr-2" />
                                            Join Waitlist
                                        </>
                                    )}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Footer Features */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-center"
                >
                    {[
                        {
                            title: "AI Agents",
                            desc: "24/7 Sales & Support",
                        },
                        {
                            title: "Automation",
                            desc: "WhatsApp & Inventory",
                        },
                        {
                            title: "Integrations",
                            desc: "QuickBooks & Sheets",
                        },
                    ].map((feature, idx) => (
                        <div key={idx} className="space-y-2">
                            <h3 className="font-semibold text-foreground">
                                {feature.title}
                            </h3>
                            <p className="text-sm text-muted-foreground">
                                {feature.desc}
                            </p>
                        </div>
                    ))}
                </motion.div>
            </main>
        </div>
    );
}
