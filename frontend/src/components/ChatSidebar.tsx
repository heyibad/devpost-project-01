import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
    MessageSquare,
    DollarSign,
    MessageCircle,
    FileText,
    Package,
    Settings,
    ChevronLeft,
    ChevronRight,
    ImageIcon,
    Menu,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import ConversationHistory from "@/components/ConversationHistory";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

interface ChatSidebarProps {
    currentPath?: string;
}

export default function ChatSidebar({
    currentPath = "/chat",
}: ChatSidebarProps) {
    const [collapsed, setCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const navigate = useNavigate();

    const menuItems = [
        {
            icon: MessageSquare,
            label: "New Chat",
            path: "/chat",
            action: "chat",
        },
        {
            icon: ImageIcon,
            label: "Campaigns",
            path: "/campaigns",
            action: "campaigns",
        },
    ];

    const agentItems = [
        {
            icon: DollarSign,
            label: "Agent Payments",
            path: "/chat/payments",
        },
        {
            icon: MessageCircle,
            label: "Sales Connector",
            path: "/chat/sales",
            badge: "Configure",
        },
        {
            icon: FileText,
            label: "Accounts Agent",
            path: "/chat/accounts",
            badge: "Configure",
        },
        {
            icon: Package,
            label: "Inventory Config",
            path: "/chat/inventory",
            badge: "Configure",
        },
    ];

    const SidebarContent = ({ isMobile = false }: { isMobile?: boolean }) => (
        <div className="flex flex-col h-full">
            <div className="p-4 flex items-center justify-between border-b border-white/20">
                {(!collapsed || isMobile) && (
                    <h2 className="font-semibold text-lg">Sahulat AI</h2>
                )}
                {!isMobile && (
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setCollapsed(!collapsed)}
                        className="ml-auto"
                    >
                        {collapsed ? (
                            <ChevronRight className="w-4 h-4" />
                        ) : (
                            <ChevronLeft className="w-4 h-4" />
                        )}
                    </Button>
                )}
            </div>

            <div className="flex-1 p-3 space-y-1 overflow-y-auto">
                {menuItems.map((item, idx) => (
                    <Button
                        key={idx}
                        variant={
                            currentPath === item.path ? "default" : "ghost"
                        }
                        className={cn(
                            "w-full justify-start",
                            collapsed && !isMobile && "justify-center px-2"
                        )}
                        onClick={() => {
                            navigate(item.path);
                            if (isMobile) setMobileOpen(false);
                        }}
                    >
                        <item.icon
                            className={cn(
                                "w-5 h-5",
                                (!collapsed || isMobile) && "mr-3"
                            )}
                        />
                        {(!collapsed || isMobile) && <span>{item.label}</span>}
                    </Button>
                ))}

                {/* Conversation History Dropdown */}
                <ConversationHistory
                    collapsed={collapsed && !isMobile}
                />

                {(!collapsed || isMobile) && (
                    <div className="pt-4 pb-2">
                        <div className="h-px bg-border mb-2" />
                    </div>
                )}

                {agentItems.map((item, idx) => (
                    <div key={idx} className="relative">
                        <Button
                            variant={
                                currentPath === item.path
                                    ? "secondary"
                                    : "ghost"
                            }
                            className={cn(
                                "w-full justify-start",
                                collapsed && !isMobile && "justify-center px-2"
                            )}
                            onClick={() => {
                                navigate(item.path);
                                if (isMobile) setMobileOpen(false);
                            }}
                        >
                            <item.icon
                                className={cn(
                                    "w-5 h-5",
                                    (!collapsed || isMobile) && "mr-3"
                                )}
                            />
                            {(!collapsed || isMobile) && (
                                <span className="flex-1 text-left">
                                    {item.label}
                                </span>
                            )}
                        </Button>
                    </div>
                ))}
            </div>

            <div className="p-3 border-t border-white/20">
                <Button
                    variant="ghost"
                    className={cn(
                        "w-full justify-start",
                        collapsed && !isMobile && "justify-center px-2"
                    )}
                    onClick={() => {
                        navigate("/chat/settings");
                        if (isMobile) setMobileOpen(false);
                    }}
                >
                    <Settings
                        className={cn(
                            "w-5 h-5",
                            (!collapsed || isMobile) && "mr-3"
                        )}
                    />
                    {(!collapsed || isMobile) && <span>Settings</span>}
                </Button>
            </div>
        </div>
    );

    return (
        <>
            {/* Mobile Trigger */}
            <div className="md:hidden fixed top-4 left-4 z-50">
                <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
                    <SheetTrigger asChild>
                        <Button
                            variant="outline"
                            size="icon"
                            className="bg-background/80 backdrop-blur-sm border-border/50"
                        >
                            <Menu className="w-5 h-5" />
                        </Button>
                    </SheetTrigger>
                    <SheetContent side="left" className="p-0 w-72 bg-background/95 backdrop-blur-xl">
                        <SidebarContent isMobile={true} />
                    </SheetContent>
                </Sheet>
            </div>

            {/* Desktop Sidebar */}
            <aside
                className={cn(
                    "hidden md:flex glass border-r border-white/20 transition-all duration-300 flex-col",
                    collapsed ? "w-16" : "w-64"
                )}
            >
                <SidebarContent />
            </aside>
        </>
    );
}
