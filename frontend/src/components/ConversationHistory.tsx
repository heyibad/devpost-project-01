import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
    History,
    Loader2,
    ChevronDown,
    ChevronRight,
    Plus,
    MessageSquare,
} from "lucide-react";
import { chatApi, type ConversationListItem } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

interface ConversationHistoryProps {
    collapsed?: boolean;
}

export default function ConversationHistory({
    collapsed = false,
}: ConversationHistoryProps) {
    const navigate = useNavigate();
    const { conversationId: currentConversationId } = useParams<{
        conversationId?: string;
    }>();
    const { toast } = useToast();

    const [conversations, setConversations] = useState<ConversationListItem[]>(
        []
    );
    const [loading, setLoading] = useState(false);
    const [expanded, setExpanded] = useState(false); // Start collapsed by default
    const [hasMore, setHasMore] = useState(false);

    const loadConversations = async (limit: number, offset: number) => {
        setLoading(true);
        try {
            const data = await chatApi.getConversations(limit, offset);

            if (offset === 0) {
                setConversations(data.conversations);
            } else {
                setConversations((prev) => [...prev, ...data.conversations]);
            }

            setHasMore(offset + data.conversations.length < data.total);
        } catch (error) {
            console.error("Failed to load conversations:", error);
            toast({
                title: "Error",
                description: "Failed to load conversation history",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    // Load conversations on mount (even when collapsed) for instant display when expanded
    useEffect(() => {
        loadConversations(5, 0);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleLoadMore = () => {
        loadConversations(20, conversations.length);
    };

    const handleConversationClick = (convId: string) => {
        navigate(`/chat/${convId}`);
    };

    const handleNewChat = () => {
        navigate("/chat");
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
        });
    };

    if (collapsed) {
        // Collapsed sidebar - show icon only, matching other sidebar buttons
        return (
            <Button
                variant="ghost"
                className={cn("w-full justify-center px-2")}
                onClick={() => setExpanded(!expanded)}
                title="History"
            >
                <History className="w-5 h-5" />
            </Button>
        );
    }

    return (
        <div className="w-full">
            {/* History Button - Matches sidebar button style */}
            <Button
                variant="ghost"
                className={cn(
                    "w-full justify-start",
                    collapsed && "justify-center px-2"
                )}
                onClick={() => setExpanded(!expanded)}
            >
                <History className={cn("w-5 h-5", !collapsed && "mr-3")} />
                {!collapsed && (
                    <>
                        <span className="flex-1 text-left">History</span>
                        {loading && conversations.length === 0 ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : expanded ? (
                            <ChevronDown className="w-4 h-4" />
                        ) : (
                            <ChevronRight className="w-4 h-4" />
                        )}
                    </>
                )}
            </Button>

            {/* Conversation List - Improved UI */}
            {expanded && (
                <div className="mt-1 space-y-1 max-h-[450px] overflow-y-auto scrollbar-thin">
                    {loading && conversations.length === 0 ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="text-center py-8 px-4">
                            <MessageSquare className="w-8 h-8 mx-auto mb-2 text-muted-foreground opacity-50" />
                            <p className="text-xs text-muted-foreground">
                                No conversations yet
                            </p>
                        </div>
                    ) : (
                        <>
                            {conversations.map((conv) => {
                                const isActive =
                                    conv.id === currentConversationId;
                                return (
                                    <button
                                        key={conv.id}
                                        onClick={() =>
                                            handleConversationClick(conv.id)
                                        }
                                        className={cn(
                                            "w-full text-left px-3 py-2.5 rounded-md transition-all duration-200",
                                            "hover:bg-accent/70 hover:shadow-sm",
                                            "focus:outline-none focus:ring-2 focus:ring-primary/20",
                                            isActive &&
                                                "bg-accent shadow-sm border border-accent-foreground/10"
                                        )}
                                    >
                                        <div className="flex items-center justify-between gap-2 mb-1.5">
                                            <span
                                                className={cn(
                                                    "text-sm font-semibold truncate flex-1",
                                                    isActive
                                                        ? "text-foreground"
                                                        : "text-foreground/90"
                                                )}
                                            >
                                                {conv.title ||
                                                    "New Conversation"}
                                            </span>
                                            <span className="text-[10px] text-muted-foreground/80 shrink-0 font-medium">
                                                {formatDate(
                                                    conv.last_message_at ||
                                                        conv.created_at
                                                )}
                                            </span>
                                        </div>
                                        {conv.last_message_preview && (
                                            <p className="text-xs text-muted-foreground/70 line-clamp-2 leading-relaxed">
                                                {conv.last_message_preview}
                                            </p>
                                        )}
                                        {conv.message_count > 0 && (
                                            <div className="flex items-center gap-1 mt-2">
                                                <MessageSquare className="w-3 h-3 text-muted-foreground/50" />
                                                <span className="text-[10px] text-muted-foreground/60">
                                                    {conv.message_count}{" "}
                                                    {conv.message_count === 1
                                                        ? "message"
                                                        : "messages"}
                                                </span>
                                            </div>
                                        )}
                                    </button>
                                );
                            })}

                            {hasMore && (
                                <div className="px-1 pt-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="w-full text-xs hover:bg-accent"
                                        onClick={handleLoadMore}
                                        disabled={loading}
                                    >
                                        {loading ? (
                                            <>
                                                <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                                                Loading more...
                                            </>
                                        ) : (
                                            <>
                                                <ChevronDown className="w-3 h-3 mr-1" />
                                                Show More
                                            </>
                                        )}
                                    </Button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}
