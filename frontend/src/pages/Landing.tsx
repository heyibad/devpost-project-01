import { useState, useEffect } from "react";
import {
    motion,
    useScroll,
    useSpring,
    useTransform,
    useMotionTemplate,
    useMotionValue,
    AnimatePresence,
} from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import AuthModal from "@/components/AuthModal";
import { useNavigate, Link } from "react-router-dom";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import {
    Sparkles,
    DollarSign,
    Package,
    TrendingUp,
    Calculator,
    MessageSquare,
    CreditCard,
    FileSpreadsheet,
    CheckCircle2,
    ArrowRight,
    Bot,
    Menu,
    Globe,
    Star,
    Zap,
    ShieldCheck,
    Users,
    Play,
    X,
} from "lucide-react";

export default function Landing() {
    const [authModal, setAuthModal] = useState<{
        open: boolean;
        mode: "login" | "signup";
    }>({
        open: false,
        mode: "login",
    });
    const [videoModal, setVideoModal] = useState(false);
    const navigate = useNavigate();
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => setScrolled(window.scrollY > 20);
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    const [isMobile, setIsMobile] = useState(false);

    useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth < 1024);
        checkMobile();
        window.addEventListener("resize", checkMobile);
        return () => window.removeEventListener("resize", checkMobile);
    }, []);

    const { scrollYProgress, scrollY } = useScroll();
    const scaleX = useSpring(scrollYProgress, {
        stiffness: 100,
        damping: 30,
        restDelta: 0.001,
    });

    const heroY = useTransform(scrollY, [0, 500], [0, 100]);
    const heroOpacity = useTransform(scrollY, [0, 800], [1, 0]);

    const fadeInUp = {
        initial: { opacity: 0, y: 20 },
        whileInView: { opacity: 1, y: 0 },
        viewport: { once: false, margin: "-100px" },
        transition: { duration: 0.7, ease: [0.21, 0.47, 0.32, 0.98] },
    };

    const agents = [
        {
            icon: MessageSquare,
            name: "Sales Agent",
            description:
                "Automate WhatsApp orders and customer communications 24/7.",
            color: "from-emerald-500 to-teal-500",
            bg: "bg-emerald-500/10",
            border: "border-emerald-500/20",
            colSpan: "md:col-span-2",
        },
        {
            icon: DollarSign,
            name: "Payment Agent",
            description:
                "Track Easypaisa and JazzCash transactions automatically.",
            color: "from-green-500 to-emerald-500",
            bg: "bg-green-500/10",
            border: "border-green-500/20",
            colSpan: "md:col-span-1",
        },
        {
            icon: Package,
            name: "Inventory Agent",
            description: "Smart stock management & alerts.",
            color: "from-teal-500 to-cyan-500",
            bg: "bg-teal-500/10",
            border: "border-teal-500/20",
            colSpan: "md:col-span-1",
        },
        {
            icon: TrendingUp,
            name: "Marketing Agent",
            description: "AI-powered social media content creation.",
            color: "from-cyan-500 to-blue-500",
            bg: "bg-cyan-500/10",
            border: "border-cyan-500/20",
            colSpan: "md:col-span-1",
        },
        {
            icon: Calculator,
            name: "Accounts Agent",
            description: "Automated bookkeeping and reports.",
            color: "from-blue-500 to-indigo-500",
            bg: "bg-blue-500/10",
            border: "border-blue-500/20",
            colSpan: "md:col-span-1",
        },
    ];

    const connectors = [
        {
            name: "WhatsApp Business",
            icon: MessageSquare,
            color: "text-green-500",
        },
        { name: "QuickBooks", icon: Calculator, color: "text-green-600" },
        {
            name: "Google Sheets",
            icon: FileSpreadsheet,
            color: "text-emerald-600",
        },
        { name: "Payment Gateway", icon: CreditCard, color: "text-teal-600" },
    ];

    const plans = [
        {
            name: "Starter",
            price: "PKR 2,999",
            period: "/month",
            description: "Perfect for small businesses just getting started.",
            features: [
                "1 AI Agent",
                "Up to 1,000 messages/month",
                "Basic analytics",
                "Email support",
            ],
        },
        {
            name: "Business",
            price: "PKR 7,999",
            period: "/month",
            description: "For growing businesses that need more power.",
            features: [
                "3 AI Agents",
                "Unlimited messages",
                "Advanced analytics",
                "Priority support",
                "Custom integrations",
            ],
            popular: true,
        },
        {
            name: "Enterprise",
            price: "Custom",
            period: "",
            description: "Tailored solutions for large organizations.",
            features: [
                "Unlimited AI Agents",
                "White-label solution",
                "Dedicated account manager",
                "Custom AI training",
                "24/7 phone support",
            ],
        },
    ];

    return (
        <div className="min-h-screen relative overflow-hidden bg-background selection:bg-primary/20 selection:text-primary font-sans">
            {/* Scroll Progress Bar */}
            <motion.div
                className="fixed top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary to-teal-500 origin-left z-[100]"
                style={{ scaleX }}
            />

            {/* Background Noise & Gradients */}
            <div className="fixed inset-0 -z-10 pointer-events-none bg-noise opacity-40" />
            <div className="fixed inset-0 -z-10 pointer-events-none overflow-hidden">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary/5 rounded-full blur-[120px] opacity-50 animate-blob" />
                <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-teal-500/5 rounded-full blur-[100px] opacity-30 animate-blob animation-delay-2000" />
                <div className="absolute top-1/2 left-0 w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-[100px] opacity-30 animate-blob animation-delay-4000" />
            </div>

            {/* Navbar */}
            <nav
                className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
                    scrolled
                        ? "bg-white/80 backdrop-blur-md border-b border-white/20 shadow-sm"
                        : "bg-transparent border-transparent"
                }`}
            >
                <div className="container mx-auto px-4 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-teal-600 flex items-center justify-center shadow-lg shadow-primary/20">
                            <Bot className="w-6 h-6 text-white" />
                        </div>
                        <span className="text-xl md:text-2xl font-bold bg-gradient-to-r from-primary to-teal-700 bg-clip-text text-transparent">
                            Sahulat AI
                        </span>
                    </div>

                    <div className="hidden md:flex items-center gap-6">
                        <a
                            href="#features"
                            className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
                        >
                            Features
                        </a>
                        <a
                            href="#pricing"
                            className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
                        >
                            Pricing
                        </a>
                        <a
                            href="#about"
                            className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
                        >
                            About
                        </a>
                    </div>

                    <div className="hidden md:flex items-center gap-4">
                        <Button
                            variant="ghost"
                            className="text-sm font-medium hover:bg-primary/5"
                            onClick={() =>
                                setAuthModal({ open: true, mode: "login" })
                            }
                        >
                            Sign In
                        </Button>
                        <Button
                            className="text-sm font-medium px-6 shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all hover:-translate-y-0.5"
                            onClick={() =>
                                setAuthModal({ open: true, mode: "signup" })
                            }
                        >
                            Get Started
                        </Button>
                    </div>

                    <div className="md:hidden">
                        <Sheet>
                            <SheetTrigger asChild>
                                <Button variant="ghost" size="icon">
                                    <Menu className="w-6 h-6" />
                                </Button>
                            </SheetTrigger>
                            <SheetContent>
                                <div className="flex flex-col gap-4 mt-8">
                                    <Button
                                        variant="ghost"
                                        onClick={() =>
                                            setAuthModal({
                                                open: true,
                                                mode: "login",
                                            })
                                        }
                                    >
                                        Sign In
                                    </Button>
                                    <Button
                                        onClick={() =>
                                            setAuthModal({
                                                open: true,
                                                mode: "signup",
                                            })
                                        }
                                    >
                                        Get Started
                                    </Button>
                                </div>
                            </SheetContent>
                        </Sheet>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-24 pb-6 px-4 lg:pt-40 lg:pb-32 relative">
                <div className="container mx-auto">
                    <div className="flex flex-col lg:flex-row items-center gap-16">
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.6 }}
                            className="flex-1 text-center lg:text-left space-y-8"
                        >
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.2 }}
                                className="inline-flex items-center gap-2 bg-white/80 backdrop-blur-sm border border-primary/20 px-4 py-1.5 rounded-full text-sm font-medium text-primary shadow-sm"
                            >
                                <Sparkles className="w-4 h-4 fill-current" />
                                <span>The Future of Business Automation</span>
                            </motion.div>

                            <h1 className="text-3xl md:text-5xl lg:text-7xl font-bold tracking-tight leading-[1.1] text-slate-900">
                                Run Your Business
                                <br />
                                <motion.span
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ duration: 0.5, delay: 0.5 }}
                                    className="bg-gradient-to-r from-primary via-teal-500 to-primary bg-clip-text text-transparent bg-[length:200%_auto] animate-gradient inline-block"
                                >
                                    On Autopilot
                                </motion.span>
                            </h1>

                            <div className="space-y-6 max-w-2xl mx-auto lg:mx-0">
                                <p className="text-lg md:text-xl text-slate-600 leading-relaxed">
                                    <span className="font-semibold text-slate-900 block mb-2">
                                        Built for World's 80% informal economy.
                                    </span>
                                    Transform your WhatsApp shop, freelance
                                    business, or local service into a smart,
                                    automated operation.
                                </p>
                                <div className="flex flex-wrap justify-center lg:justify-start gap-3 text-sm font-medium text-slate-600">
                                    <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
                                        <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                                        Inventory
                                    </span>
                                    <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
                                        <MessageSquare className="w-4 h-4 text-green-600" />
                                        Sales
                                    </span>
                                    <span className="flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
                                        <Calculator className="w-4 h-4 text-blue-600" />
                                        Accounts
                                    </span>
                                </div>
                            </div>

                            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
                                <motion.div
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                >
                                    <Button
                                        size="lg"
                                        className="w-full sm:w-auto text-lg h-14 px-8 shadow-xl shadow-primary/20 hover:shadow-primary/30 transition-all rounded-2xl"
                                        onClick={() =>
                                            setAuthModal({
                                                open: true,
                                                mode: "signup",
                                            })
                                        }
                                    >
                                        Start Free Trial
                                        <ArrowRight className="w-5 h-5 ml-2" />
                                    </Button>
                                </motion.div>
                                <Button
                                    size="lg"
                                    variant="outline"
                                    className="w-full sm:w-auto text-lg h-14 px-8 bg-white/50 backdrop-blur-sm border-slate-200 hover:bg-white/80 rounded-2xl group"
                                    onClick={() => setVideoModal(true)}
                                >
                                    <Play className="w-5 h-5 mr-2 group-hover:text-primary transition-colors" />
                                    Watch Demo
                                </Button>
                            </div>

                            <div className="pt-2 flex items-center justify-center lg:justify-start gap-8 text-sm text-slate-500">
                                <div className="flex items-center gap-2">
                                    <ShieldCheck className="w-4 h-4 text-primary" />
                                    <span>Enterprise-grade security</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Users className="w-4 h-4 text-primary" />
                                    <span>Trusted by 500+ businesses</span>
                                </div>
                            </div>
                        </motion.div>

                        {/* Hero Visual */}
                        <motion.div
                            style={
                                isMobile
                                    ? {}
                                    : { y: heroY, opacity: heroOpacity }
                            }
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 1, ease: "easeOut" }}
                            className="flex-1 w-full max-w-[600px] lg:max-w-none perspective-1000 mt-16 lg:mt-0"
                        >
                            <motion.div
                                animate={{ y: [0, -15, 0] }}
                                transition={{
                                    duration: 6,
                                    repeat: Infinity,
                                    ease: "easeInOut",
                                }}
                                className="relative transform lg:rotate-y-12 lg:rotate-x-6 hover:rotate-0 transition-all duration-700 ease-out"
                            >
                                <div className="absolute inset-0 bg-gradient-to-tr from-primary/20 to-teal-500/20 rounded-[2rem] blur-3xl -z-10" />
                                <div className="bg-white/90 backdrop-blur-xl border border-white/50 rounded-[2rem] p-2 shadow-2xl shadow-black/10">
                                    <div className="bg-slate-50 rounded-[1.5rem] overflow-hidden border border-slate-100">
                                        <div className="h-12 border-b border-slate-200 bg-white flex items-center px-4 md:px-6 justify-between">
                                            <div className="flex gap-2">
                                                <div className="w-3 h-3 rounded-full bg-red-400" />
                                                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                                                <div className="w-3 h-3 rounded-full bg-green-400" />
                                            </div>
                                            <div className="text-xs font-medium text-slate-400">
                                                sahulat-ai.dashboard
                                            </div>
                                        </div>
                                        <div className="p-4 md:p-8 grid grid-cols-2 gap-3 md:gap-6">
                                            <div className="col-span-2 h-auto md:h-32 bg-white rounded-xl border border-slate-100 shadow-sm p-4 md:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                                                <div>
                                                    <div className="text-sm text-slate-500 mb-1">
                                                        Total Revenue
                                                    </div>
                                                    <div className="text-xl md:text-3xl font-bold text-slate-900">
                                                        PKR 1,240,500
                                                    </div>
                                                    <div className="text-xs text-emerald-600 font-medium mt-1">
                                                        +12.5% from last month
                                                    </div>
                                                </div>
                                                <div className="w-10 h-10 md:w-12 md:h-12 rounded-full bg-emerald-50 flex items-center justify-center self-end md:self-center">
                                                    <TrendingUp className="w-5 h-5 md:w-6 md:h-6 text-emerald-600" />
                                                </div>
                                            </div>
                                            <div className="h-auto md:h-32 bg-white rounded-xl border border-slate-100 shadow-sm p-4 md:p-6">
                                                <div className="w-8 h-8 md:w-10 md:h-10 rounded-lg bg-blue-50 flex items-center justify-center mb-2 md:mb-4">
                                                    <MessageSquare className="w-4 h-4 md:w-5 md:h-5 text-blue-600" />
                                                </div>
                                                <div className="text-lg md:text-2xl font-bold text-slate-900">
                                                    1,402
                                                </div>
                                                <div className="text-[10px] md:text-xs text-slate-500">
                                                    Active Conversations
                                                </div>
                                            </div>
                                            <div className="h-auto md:h-32 bg-white rounded-xl border border-slate-100 shadow-sm p-4 md:p-6">
                                                <div className="w-8 h-8 md:w-10 md:h-10 rounded-lg bg-purple-50 flex items-center justify-center mb-2 md:mb-4">
                                                    <Package className="w-4 h-4 md:w-5 md:h-5 text-purple-600" />
                                                </div>
                                                <div className="text-lg md:text-2xl font-bold text-slate-900">
                                                    89%
                                                </div>
                                                <div className="text-[10px] md:text-xs text-slate-500">
                                                    Inventory Health
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Trusted By Strip */}
            <section className="py-6 md:py-10 border-y border-slate-200 bg-slate-50/50">
                <div className="container mx-auto px-4">
                    <p className="text-center text-sm font-semibold text-slate-500 mb-8 uppercase tracking-wider">
                        Trusted by innovative companies across Pakistan
                    </p>
                    <div className="relative flex overflow-x-hidden group">
                        <div className="animate-marquee whitespace-nowrap flex gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
                            {[...Array(2)].map((_, i) => (
                                <div key={i} className="flex gap-12">
                                    {[
                                        "TechFlow",
                                        "ShopifyPk",
                                        "DarazHub",
                                        "RetailPro",
                                        "EasyStore",
                                        "KarachiMart",
                                        "LahoreTraders",
                                    ].map((logo) => (
                                        <div
                                            key={logo}
                                            className="text-xl font-bold text-slate-800 flex items-center gap-2 mx-4"
                                        >
                                            <div className="w-6 h-6 rounded bg-slate-800" />
                                            {logo}
                                        </div>
                                    ))}
                                </div>
                            ))}
                        </div>
                        <div className="absolute top-0 animate-marquee2 whitespace-nowrap flex gap-12 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
                            {[...Array(2)].map((_, i) => (
                                <div key={i} className="flex gap-12">
                                    {[
                                        "TechFlow",
                                        "ShopifyPk",
                                        "DarazHub",
                                        "RetailPro",
                                        "EasyStore",
                                        "KarachiMart",
                                        "LahoreTraders",
                                    ].map((logo) => (
                                        <div
                                            key={logo}
                                            className="text-xl font-bold text-slate-800 flex items-center gap-2 mx-4"
                                        >
                                            <div className="w-6 h-6 rounded bg-slate-800" />
                                            {logo}
                                        </div>
                                    ))}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* Bento Grid Agents */}
            <section id="features" className="py-10 md:py-24 px-4 bg-white">
                <div className="container mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: false, margin: "-100px" }}
                        className="text-center mb-16 max-w-3xl mx-auto"
                    >
                        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900 mb-4">
                            A Complete Workforce in the Cloud
                        </h2>
                        <p className="text-lg text-slate-600">
                            Replace fragmented tools with a unified team of AI
                            agents. Each agent is specialized, trained, and
                            ready to work 24/7.
                        </p>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {agents.map((agent, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: false, margin: "-50px" }}
                                transition={{ delay: idx * 0.1 }}
                                className={agent.colSpan}
                            >
                                <Card className="group relative overflow-hidden border-slate-200 bg-slate-50/50 hover:bg-white transition-all duration-500 hover:shadow-2xl hover:-translate-y-2 h-full">
                                    <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                    <div className="absolute -inset-px bg-gradient-to-r from-primary/20 to-teal-500/20 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 -z-10 blur-sm" />
                                    <div className="p-5 md:p-8 relative z-10 h-full flex flex-col">
                                        <div
                                            className={`w-14 h-14 rounded-2xl ${agent.bg} ${agent.border} border flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}
                                        >
                                            <agent.icon className="w-7 h-7 text-primary" />
                                        </div>
                                        <h3 className="text-2xl font-bold mb-3 text-slate-900">
                                            {agent.name}
                                        </h3>
                                        <p className="text-slate-600 leading-relaxed mb-6 flex-1">
                                            {agent.description}
                                        </p>
                                        <div className="flex items-center text-primary font-medium text-sm group-hover:translate-x-1 transition-transform cursor-pointer">
                                            Learn more{" "}
                                            <ArrowRight className="w-4 h-4 ml-1" />
                                        </div>
                                    </div>
                                </Card>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Feature Deep Dive */}
            <section className="py-16 md:py-24 px-4 bg-slate-50">
                <div className="container mx-auto space-y-24">
                    {/* Feature 1 */}
                    <div className="flex flex-col lg:flex-row items-center gap-16">
                        <motion.div
                            initial={{ opacity: 0, x: -50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: false, margin: "-100px" }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className="flex-1 space-y-6"
                        >
                            <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
                                <MessageSquare className="w-6 h-6 text-blue-600" />
                            </div>
                            <h3 className="text-2xl md:text-3xl font-bold text-slate-900">
                                Conversational Commerce
                            </h3>
                            <p className="text-lg text-slate-600 leading-relaxed">
                                Turn every WhatsApp conversation into a sale.
                                Our Sales Agent understands context, recommends
                                products, and processes orders automatically.
                                It's like having your best salesperson working
                                24/7.
                            </p>
                            <ul className="space-y-3">
                                {[
                                    "Auto-reply to inquiries",
                                    "Catalog integration",
                                    "Order confirmation & tracking",
                                ].map((item) => (
                                    <li
                                        key={item}
                                        className="flex items-center gap-3 text-slate-700"
                                    >
                                        <CheckCircle2 className="w-5 h-5 text-primary" />
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </motion.div>
                        <motion.div
                            initial={{ opacity: 0, x: 50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: false, margin: "-100px" }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className="flex-1 bg-white rounded-2xl p-5 md:p-8 shadow-xl border border-slate-100"
                        >
                            {/* Abstract UI representation */}
                            <div className="space-y-4">
                                <div className="flex gap-4">
                                    <div className="w-8 h-8 rounded-full bg-slate-200" />
                                    <div className="bg-slate-100 p-3 rounded-2xl rounded-tl-none max-w-[80%]">
                                        <p className="text-sm text-slate-600">
                                            Do you have the black leather jacket
                                            in medium?
                                        </p>
                                    </div>
                                </div>
                                <div className="flex gap-4 flex-row-reverse">
                                    <div className="w-8 h-8 rounded-full bg-primary/20" />
                                    <div className="bg-primary/10 p-3 rounded-2xl rounded-tr-none max-w-[80%]">
                                        <p className="text-sm text-slate-800">
                                            Yes! We have 3 left in stock. Would
                                            you like to see some photos?
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>

                    {/* Feature 2 */}
                    <div className="flex flex-col lg:flex-row-reverse items-center gap-16">
                        <motion.div
                            initial={{ opacity: 0, x: 50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: false, margin: "-100px" }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className="flex-1 space-y-6"
                        >
                            <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
                                <Calculator className="w-6 h-6 text-emerald-600" />
                            </div>
                            <h3 className="text-2xl md:text-3xl font-bold text-slate-900">
                                Financial Clarity
                            </h3>
                            <p className="text-lg text-slate-600 leading-relaxed">
                                Stop guessing your profits. Our Accounts Agent
                                tracks every rupee from Easypaisa, JazzCash, and
                                bank transfers. Get daily P&L reports delivered
                                straight to your phone.
                            </p>
                            <ul className="space-y-3">
                                {[
                                    "Automated expense tracking",
                                    "Real-time revenue dashboard",
                                    "Tax-ready reports",
                                ].map((item) => (
                                    <li
                                        key={item}
                                        className="flex items-center gap-3 text-slate-700"
                                    >
                                        <CheckCircle2 className="w-5 h-5 text-primary" />
                                        {item}
                                    </li>
                                ))}
                            </ul>
                        </motion.div>
                        <motion.div
                            initial={{ opacity: 0, x: -50 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: false, margin: "-100px" }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className="flex-1 bg-white rounded-2xl p-6 md:p-8 shadow-xl border border-slate-100"
                        >
                            <div className="space-y-4">
                                <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                                    <span className="font-medium text-slate-600">
                                        Net Profit (This Month)
                                    </span>
                                    <span className="font-bold text-emerald-600 text-xl">
                                        + PKR 450,000
                                    </span>
                                </div>
                                <div className="h-32 bg-slate-50 rounded-lg flex items-end justify-between p-4 gap-2">
                                    {[40, 60, 45, 70, 85, 65, 90].map(
                                        (h, i) => (
                                            <motion.div
                                                key={i}
                                                initial={{ height: 0 }}
                                                whileInView={{
                                                    height: `${h}%`,
                                                }}
                                                viewport={{ once: false }}
                                                transition={{
                                                    delay: i * 0.1,
                                                    duration: 0.5,
                                                }}
                                                className="w-full bg-primary/80 rounded-t-sm"
                                            />
                                        )
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Testimonials */}
            <section className="py-16 md:py-24 px-4 bg-white">
                <div className="container mx-auto">
                    <motion.h2
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: false, margin: "-100px" }}
                        className="text-2xl md:text-3xl font-bold text-center mb-16"
                    >
                        Loved by Business Owners
                    </motion.h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {[
                            {
                                name: "Sarah Ahmed",
                                role: "Owner, Glow Cosmetics",
                                quote: "Managing orders on WhatsApp was a nightmare before Sahulat AI. Now, the Sales Agent handles everything automatically. My sales have increased by 40%!",
                                initial: "SA",
                                color: "bg-pink-100 text-pink-600",
                            },
                            {
                                name: "Bilal Siddiqui",
                                role: "Founder, TechGadgets PK",
                                quote: "The Inventory Agent is a lifesaver. I get alerts before I run out of stock, and the integration with Google Sheets makes accounting so much easier.",
                                initial: "BS",
                                color: "bg-blue-100 text-blue-600",
                            },
                            {
                                name: "Zainab Malik",
                                role: "Creative Director, ZM Designs",
                                quote: "I was skeptical about AI, but Sahulat AI is so easy to use. It feels like I have a full support team working 24/7 without the overhead costs.",
                                initial: "ZM",
                                color: "bg-purple-100 text-purple-600",
                            },
                        ].map((testimonial, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: false, margin: "-50px" }}
                                transition={{ delay: idx * 0.1 }}
                            >
                                <Card className="p-5 md:p-8 border-slate-100 bg-slate-50/30 hover:bg-white transition-colors h-full flex flex-col">
                                    <div className="flex gap-1 mb-4">
                                        {[1, 2, 3, 4, 5].map((star) => (
                                            <Star
                                                key={star}
                                                className="w-4 h-4 fill-yellow-400 text-yellow-400"
                                            />
                                        ))}
                                    </div>
                                    <p className="text-slate-600 mb-6 italic flex-1">
                                        "{testimonial.quote}"
                                    </p>
                                    <div className="flex items-center gap-3">
                                        <div
                                            className={`w-10 h-10 rounded-full ${testimonial.color} flex items-center justify-center font-bold text-sm`}
                                        >
                                            {testimonial.initial}
                                        </div>
                                        <div>
                                            <div className="font-bold text-slate-900">
                                                {testimonial.name}
                                            </div>
                                            <div className="text-xs text-slate-500">
                                                {testimonial.role}
                                            </div>
                                        </div>
                                    </div>
                                </Card>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Pricing Section */}
            <section
                id="pricing"
                className="py-16 md:py-24 px-4 bg-slate-900 text-white relative overflow-hidden"
            >
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20" />
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />

                <div className="container mx-auto relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: false, margin: "-100px" }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6">
                            Simple, Transparent Pricing
                        </h2>
                        <p className="text-xl text-slate-300 max-w-2xl mx-auto">
                            Start small and scale as you grow. No hidden fees.
                        </p>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                        {plans.map((plan, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: false, margin: "-50px" }}
                                transition={{ delay: idx * 0.1 }}
                            >
                                <Card
                                    className={`relative p-5 md:p-8 transition-all duration-300 border-0 ${
                                        plan.popular
                                            ? "bg-white text-slate-900 shadow-2xl scale-105 z-10"
                                            : "bg-white/10 backdrop-blur-md text-white hover:bg-white/15"
                                    }`}
                                >
                                    {plan.popular && (
                                        <div className="absolute -top-5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-primary to-teal-600 text-white px-6 py-1.5 rounded-full text-sm font-bold shadow-lg shadow-primary/20">
                                            Most Popular
                                        </div>
                                    )}

                                    <div className="mb-8">
                                        <h3 className="text-2xl font-bold mb-2">
                                            {plan.name}
                                        </h3>
                                        <p
                                            className={`text-sm mb-6 ${
                                                plan.popular
                                                    ? "text-slate-500"
                                                    : "text-slate-300"
                                            }`}
                                        >
                                            {plan.description}
                                        </p>
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-4xl font-bold tracking-tight">
                                                {plan.price}
                                            </span>
                                            <span
                                                className={`font-medium ${
                                                    plan.popular
                                                        ? "text-slate-500"
                                                        : "text-slate-300"
                                                }`}
                                            >
                                                {plan.period}
                                            </span>
                                        </div>
                                    </div>

                                    <ul className="space-y-4 mb-8">
                                        {plan.features.map((feature, fidx) => (
                                            <li
                                                key={fidx}
                                                className="flex items-start gap-3"
                                            >
                                                <div
                                                    className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                                                        plan.popular
                                                            ? "bg-primary/10"
                                                            : "bg-white/10"
                                                    }`}
                                                >
                                                    <CheckCircle2
                                                        className={`w-4 h-4 ${
                                                            plan.popular
                                                                ? "text-primary"
                                                                : "text-white"
                                                        }`}
                                                    />
                                                </div>
                                                <span
                                                    className={`text-sm font-medium ${
                                                        plan.popular
                                                            ? "text-slate-600"
                                                            : "text-slate-300"
                                                    }`}
                                                >
                                                    {feature}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>

                                    <Button
                                        className={`w-full h-12 text-base ${
                                            plan.popular
                                                ? "shadow-lg shadow-primary/20 hover:shadow-primary/30"
                                                : "bg-white/20 hover:bg-white/30 text-white border-0"
                                        }`}
                                        variant={
                                            plan.popular ? "default" : "outline"
                                        }
                                        onClick={() =>
                                            setAuthModal({
                                                open: true,
                                                mode: "signup",
                                            })
                                        }
                                    >
                                        Get Started
                                    </Button>
                                </Card>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-16 md:py-24 px-4">
                <div className="container mx-auto max-w-5xl">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: false, margin: "-100px" }}
                        transition={{ duration: 0.5 }}
                        className="bg-gradient-to-br from-primary to-teal-600 rounded-[2.5rem] p-6 md:p-20 text-center text-white relative overflow-hidden shadow-2xl shadow-primary/30"
                    >
                        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay" />
                        <div className="relative z-10 space-y-8">
                            <h2 className="text-3xl md:text-4xl lg:text-6xl font-bold tracking-tight">
                                Ready to automate your business?
                            </h2>
                            <p className="text-xl text-white/90 max-w-2xl mx-auto">
                                Join hundreds of Pakistani entrepreneurs who are
                                saving time and making more money with Sahulat
                                AI.
                            </p>
                            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                                <Button
                                    size="lg"
                                    className="h-14 px-8 text-lg bg-white text-primary hover:bg-white/90 shadow-xl"
                                    onClick={() =>
                                        setAuthModal({
                                            open: true,
                                            mode: "signup",
                                        })
                                    }
                                >
                                    Get Started Now
                                </Button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 px-4 border-t border-slate-200 bg-slate-50">
                <div className="container mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
                        <div className="col-span-1 md:col-span-2">
                            <div className="flex items-center gap-2 mb-6">
                                <Bot className="w-8 h-8 text-primary" />
                                <span className="text-xl font-bold text-slate-900">
                                    Sahulat AI
                                </span>
                            </div>
                            <p className="text-slate-500 max-w-sm">
                                Empowering Pakistan's entrepreneurs with
                                intelligent automation tools. Build, grow, and
                                scale your business with AI.
                            </p>
                        </div>
                        <div>
                            <h4 className="font-bold mb-6 text-slate-900">
                                Product
                            </h4>
                            <ul className="space-y-4 text-sm text-slate-500">
                                <li className="hover:text-primary cursor-pointer">
                                    Features
                                </li>
                                <li className="hover:text-primary cursor-pointer">
                                    Pricing
                                </li>
                                <li className="hover:text-primary cursor-pointer">
                                    Integrations
                                </li>
                                <li className="hover:text-primary cursor-pointer">
                                    Enterprise
                                </li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold mb-6 text-slate-900">
                                Company
                            </h4>
                            <ul className="space-y-4 text-sm text-slate-500">
                                <li className="hover:text-primary cursor-pointer">
                                    About Us
                                </li>
                                <li className="hover:text-primary cursor-pointer">
                                    Contact
                                </li>
                                <li>
                                    <Link
                                        to="/privacy-policy"
                                        className="hover:text-primary transition-colors"
                                    >
                                        Privacy Policy
                                    </Link>
                                </li>
                                <li>
                                    <Link
                                        to="/terms"
                                        className="hover:text-primary transition-colors"
                                    >
                                        Terms of Service
                                    </Link>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <div className="pt-8 border-t border-slate-200 text-center text-sm text-slate-500">
                        <p>&copy; 2025 Sahulat AI. Made with ❤️ in Pakistan.</p>
                    </div>
                </div>
            </footer>

            {/* Video Modal */}
            <AnimatePresence>
                {videoModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
                        onClick={() => setVideoModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            transition={{
                                type: "spring",
                                damping: 25,
                                stiffness: 300,
                            }}
                            className="relative w-full max-w-4xl aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button
                                onClick={() => setVideoModal(false)}
                                className="absolute -top-12 right-0 md:top-4 md:right-4 z-10 w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-sm flex items-center justify-center transition-colors"
                            >
                                <X className="w-5 h-5 text-white" />
                            </button>
                            <iframe
                                src="https://www.youtube.com/embed/vww9NZNkNIQ?autoplay=1&rel=0"
                                title="Sahulat AI Demo"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                                className="w-full h-full"
                            />
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <AuthModal
                open={authModal.open}
                onClose={() => setAuthModal({ ...authModal, open: false })}
                mode={authModal.mode}
                onSuccess={() => navigate("/chat")}
            />
        </div>
    );
}
