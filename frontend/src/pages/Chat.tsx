import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import ChatSidebar from "@/components/ChatSidebar";
import ConnectedToolsPopup from "@/components/ConnectedToolsPopup";
import { Send, Loader2, Bot, User } from "lucide-react";
import { chatApi, type ChatMessage } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useParams, useNavigate } from "react-router-dom";

interface Message {
    role: "user" | "assistant";
    content: string;
    id: string;
}

export default function Chat() {
    const { conversationId: urlConversationId } = useParams<{
        conversationId?: string;
    }>();
    const navigate = useNavigate();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { toast } = useToast();

    // ULTRA-OPTIMIZED: Memoized scroll function
    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    // Load conversation from URL when component mounts or URL changes
    useEffect(() => {
        const loadConversation = async () => {
            if (urlConversationId) {
                // If URL has a conversation ID different from current, load it
                if (urlConversationId !== conversationId) {
                    setLoadingHistory(true);
                    try {
                        const conversation = await chatApi.getConversation(
                            urlConversationId
                        );

                        // Convert messages to component format
                        const loadedMessages: Message[] =
                            conversation.messages.map((msg) => ({
                                id: msg.id,
                                role: msg.role as "user" | "assistant",
                                content: msg.content,
                            }));

                        setMessages(loadedMessages);
                        setConversationId(conversation.id);
                    } catch (error) {
                        console.error("Failed to load conversation:", error);
                        toast({
                            title: "Error",
                            description: "Failed to load conversation history",
                            variant: "destructive",
                        });
                        // Navigate back to new chat if conversation not found
                        navigate("/chat");
                    } finally {
                        setLoadingHistory(false);
                    }
                }
            } else if (!urlConversationId && conversationId) {
                // If URL is /chat (no ID) but we have a conversationId, start new chat
                setMessages([]);
                setConversationId(null);
            }
        };

        loadConversation();
    }, [urlConversationId, conversationId, navigate, toast]);

    // ULTRA-OPTIMIZED: useCallback to prevent re-creating function on every render
    const handleSend = useCallback(async () => {
        if (!input.trim() || loading) return;

        const userInput = input.trim();
        const userMessage: Message = {
            role: "user",
            content: userInput,
            id: Date.now().toString(),
        };

        // ULTRA-OPTIMIZED: Clear input immediately for instant feedback
        setInput("");
        setMessages((prev) => [...prev, userMessage]);
        setLoading(true);

        // Add thinking indicator
        const thinkingId = (Date.now() + 1).toString();
        setMessages((prev) => [
            ...prev,
            { role: "assistant", content: "", id: thinkingId },
        ]);

        try {
            let assistantContent = "";
            let updateCounter = 0;
            let lastUpdateTime = Date.now();

            // ULTRA-OPTIMIZED: Build message history ONCE before streaming
            // Limit to last 15 messages for even faster processing
            const allMessages = [...messages, userMessage];
            const recentMessages = allMessages.slice(-15); // Reduced from 20 to 15 for speed
            const messageHistory: ChatMessage[] = recentMessages.map((msg) => ({
                role: msg.role,
                content: msg.content,
            }));

            await chatApi.stream(
                messageHistory,
                conversationId,
                (chunk: string) => {
                    assistantContent += chunk;
                    updateCounter++;
                    const now = Date.now();

                    // ULTRA-OPTIMIZED: Time-based + count-based batching for smoother updates
                    // Update every 50ms OR every 2 chunks (whichever comes first)
                    const shouldUpdate =
                        now - lastUpdateTime >= 50 || updateCounter % 2 === 0;

                    if (shouldUpdate) {
                        lastUpdateTime = now;
                        setMessages((prev) => {
                            const newMessages = [...prev];
                            const lastMessage =
                                newMessages[newMessages.length - 1];
                            if (lastMessage.id === thinkingId) {
                                lastMessage.content = assistantContent;
                            }
                            return newMessages;
                        });
                    }
                },
                (snapshot) => {
                    // Extract conversation ID from snapshot and navigate to conversation URL
                    if (!conversationId && snapshot.conversation) {
                        const newConvId = snapshot.conversation.id;
                        setConversationId(newConvId);
                        // Navigate to conversation URL without reloading
                        navigate(`/chat/${newConvId}`, { replace: true });
                    }
                }
            );

            // ULTRA-OPTIMIZED: Final update to ensure all content is displayed
            setMessages((prev) => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage.id === thinkingId) {
                    lastMessage.content = assistantContent;
                }
                return newMessages;
            });
        } catch (error: unknown) {
            const errorMessage =
                error instanceof Error
                    ? error.message
                    : "Failed to send message";
            toast({
                title: "Error",
                description: errorMessage,
                variant: "destructive",
            });

            // Remove thinking message on error
            setMessages((prev) => prev.filter((m) => m.id !== thinkingId));
        } finally {
            setLoading(false);
        }
    }, [input, loading, messages, conversationId, toast, navigate]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex h-screen w-full">
            <ChatSidebar currentPath="/chat" />

            <main className="flex-1 flex flex-col bg-gradient-to-b from-background to-secondary/20">
                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto p-4 pt-16 md:pt-4 space-y-6">
                    {loadingHistory ? (
                        <div className="h-full flex items-center justify-center">
                            <div className="text-center space-y-4">
                                <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
                                <p className="text-muted-foreground">
                                    Loading conversation...
                                </p>
                            </div>
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="h-full flex items-center justify-center">
                            <div className="text-center space-y-4 max-w-md">
                                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                                    <Bot className="w-8 h-8 text-primary" />
                                </div>
                                <h2 className="text-2xl font-bold">
                                    Welcome to Sahulat AI
                                </h2>
                                <p className="text-muted-foreground">
                                    Ask me anything about your business. I can
                                    help with sales, payments, inventory, and
                                    more.
                                </p>
                            </div>
                        </div>
                    ) : (
                        messages.map((message) => (
                            <div
                                key={message.id}
                                className={`flex gap-3 ${message.role === "user"
                                        ? "justify-end"
                                        : "justify-start"
                                    }`}
                            >
                                {message.role === "assistant" && (
                                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                        <Bot className="w-5 h-5 text-primary" />
                                    </div>
                                )}

                                <div
                                    className={`max-w-[70%] rounded-2xl px-4 py-3 ${message.role === "user"
                                            ? "bg-primary text-primary-foreground"
                                            : "glass"
                                        }`}
                                >
                                    {message.content ? (
                                        <div className="prose prose-sm dark:prose-invert max-w-none">
                                            <ReactMarkdown
                                                remarkPlugins={[remarkGfm]}
                                            >
                                                {message.content}
                                            </ReactMarkdown>
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-2">
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            <span className="text-sm text-muted-foreground">
                                                Thinking...
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {message.role === "user" && (
                                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0">
                                        <User className="w-5 h-5" />
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="border-t border-border/50 p-4 glass">
                    <div className="max-w-4xl mx-auto flex items-end gap-3">
                        <Textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Type your message..."
                            className="glass resize-none min-h-[60px] max-h-[200px]"
                            disabled={loading}
                        />

                        <div className="flex items-center gap-2">
                            <ConnectedToolsPopup />
                            <Button
                                onClick={handleSend}
                                disabled={!input.trim() || loading}
                                size="icon"
                                className="h-[60px] w-[60px]"
                            >
                                {loading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Send className="w-5 h-5" />
                                )}
                            </Button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
