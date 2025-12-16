import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import ChatSidebar from "@/components/ChatSidebar";
import { usePosters, type PosterGeneration } from "@/hooks/use-posters";
import { useToast } from "@/hooks/use-toast";
import {
    Copy,
    ChevronLeft,
    ChevronRight,
    Facebook,
    Twitter,
    Linkedin,
    Instagram,
    Calendar,
} from "lucide-react";
import { cn } from "@/lib/utils";

const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
};

export default function Campaigns() {
    const [page, setPage] = useState(1);
    const pageSize = 12;
    const { posters, loading, error, totalPages, total } = usePosters(
        page,
        pageSize
    );
    const { toast } = useToast();

    const captionedCount = posters.filter((poster) =>
        poster.image_caption?.trim()
    ).length;
    const shareReadyPercent =
        total > 0 ? Math.round((captionedCount / total) * 100) : 0;
    const latestPosterDate = posters.length
        ? formatDate(posters[0].created_at)
        : "—";

    const sharePlatforms = [
        {
            key: "facebook" as const,
            label: "Facebook",
            icon: Facebook,
            className: "text-[#1877F2]",
        },
        {
            key: "twitter" as const,
            label: "Twitter",
            icon: Twitter,
            className: "text-[#1DA1F2]",
        },
        {
            key: "linkedin" as const,
            label: "LinkedIn",
            icon: Linkedin,
            className: "text-[#0A66C2]",
        },
        {
            key: "instagram" as const,
            label: "Instagram",
            icon: Instagram,
            className: "text-[#D62976]",
        },
    ];

    const handleCopyCaption = async (caption: string | null) => {
        if (!caption) {
            toast({
                title: "No caption",
                description: "This poster doesn't have a caption to copy.",
                variant: "destructive",
            });
            return;
        }

        try {
            await navigator.clipboard.writeText(caption);
            toast({
                title: "Caption copied!",
                description: "The caption has been copied to your clipboard.",
            });
        } catch (err) {
            toast({
                title: "Copy failed",
                description: "Failed to copy caption to clipboard.",
                variant: "destructive",
            });
        }
    };

    const shareToSocialMedia = async (
        poster: PosterGeneration,
        platform: "facebook" | "twitter" | "linkedin" | "instagram"
    ) => {
        const caption = poster.image_caption || "";
        const imageUrl = poster.image_url;

        // Create shareable content
        let shareUrl = "";

        switch (platform) {
            case "facebook":
                // Facebook doesn't support pre-filling with image URL in the new sharing API
                // Users will need to manually attach the image
                shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(
                    imageUrl
                )}&quote=${encodeURIComponent(caption)}`;
                break;

            case "twitter":
                shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(
                    caption
                )}&url=${encodeURIComponent(imageUrl)}`;
                break;

            case "linkedin":
                shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(
                    imageUrl
                )}`;
                break;

            case "instagram":
                // Instagram doesn't support web sharing directly
                // Copy image URL and caption for manual posting
                try {
                    await navigator.clipboard.writeText(
                        `${caption}\n\nImage URL: ${imageUrl}`
                    );
                    toast({
                        title: "Instagram sharing",
                        description:
                            "Caption and image URL copied! Open Instagram app to post.",
                    });
                    return;
                } catch (err) {
                    toast({
                        title: "Copy failed",
                        description: "Failed to copy content for Instagram.",
                        variant: "destructive",
                    });
                    return;
                }

            default:
                return;
        }

        // Open share URL in new window
        window.open(shareUrl, "_blank", "width=600,height=400");

        toast({
            title: "Opening share dialog",
            description: `Sharing to ${platform}...`,
        });
    };

    return (
        <div className="flex min-h-screen bg-[#f5faf6]">
            <ChatSidebar currentPath="/campaigns" />

            <main className="relative flex-1 overflow-y-auto bg-gradient-to-b from-white via-white to-[#e8f5ee]">
                <div className="absolute inset-x-10 top-0 h-40 rounded-b-[64px] bg-emerald-100/40 blur-3xl" />
                <div className="relative z-10 container mx-auto p-6 pt-16 md:pt-6 max-w-6xl space-y-8">
                    {/* Hero */}
                    <section className="rounded-[28px] border border-emerald-100/60 bg-white/90 px-8 py-10 shadow-[0_18px_50px_rgba(16,185,129,0.12)] backdrop-blur">
                        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
                            <div className="space-y-4 max-w-3xl">
                                <p className="text-sm font-semibold uppercase tracking-[0.25em] text-emerald-500">
                                    Campaign Library
                                </p>
                                <h1 className="text-4xl font-semibold text-emerald-950 tracking-tight">
                                    Sleek social drops ready to post in one
                                    click
                                </h1>
                                <p className="text-base text-muted-foreground">
                                    Browse every AI generated poster in a clean,
                                    distraction-free wall. Each asset keeps your
                                    brand voice, includes a caption, and
                                    launches the right network instantly.
                                </p>
                            </div>
                            {total > 0 && (
                                <div className="rounded-2xl border border-emerald-100/80 bg-white/80 px-5 py-4 text-sm text-muted-foreground shadow-sm">
                                    <p className="font-medium text-emerald-700">
                                        {total} poster{total !== 1 ? "s" : ""}{" "}
                                        available
                                    </p>
                                    <p>Latest drop · {latestPosterDate}</p>
                                    <p>{shareReadyPercent}% caption ready</p>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Error State */}
                    {error && (
                        <Card className="border-red-200 bg-red-50">
                            <CardContent className="pt-6">
                                <p className="text-red-600 text-center">
                                    {error}
                                </p>
                            </CardContent>
                        </Card>
                    )}

                    {/* Loading State */}
                    {loading && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            {[...Array(pageSize)].map((_, i) => (
                                <Card key={i} className="overflow-hidden">
                                    <Skeleton className="h-64 w-full" />
                                    <CardContent className="p-4">
                                        <Skeleton className="h-4 w-3/4 mb-2" />
                                        <Skeleton className="h-4 w-1/2" />
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}

                    {/* Empty State */}
                    {!loading && !error && posters.length === 0 && (
                        <Card className="border-dashed">
                            <CardContent className="pt-12 pb-12 text-center">
                                <div className="flex flex-col items-center gap-4">
                                    <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center">
                                        <Calendar className="w-8 h-8 text-purple-600" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold mb-2">
                                            No campaigns yet
                                        </h3>
                                        <p className="text-muted-foreground max-w-md">
                                            Generate your first marketing poster
                                            using the AI chat to see it here.
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Posters Grid */}
                    {!loading && !error && posters.length > 0 && (
                        <>
                            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
                                {posters.map((poster) => (
                                    <article
                                        key={poster.id}
                                        className="group flex h-full flex-col overflow-hidden rounded-[28px] border border-emerald-100/70 bg-white/90 shadow-[0_20px_45px_rgba(16,185,129,0.08)] transition-transform duration-500 hover:-translate-y-2"
                                    >
                                        <div className="relative aspect-[4/5] overflow-hidden">
                                            <img
                                                src={poster.image_url}
                                                alt={
                                                    poster.image_caption ||
                                                    "Generated poster"
                                                }
                                                className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
                                                loading="lazy"
                                            />
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-black/0 to-black/10 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
                                            <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-full bg-black/60 px-3 py-1 text-xs font-medium text-white/90">
                                                <Calendar className="h-3.5 w-3.5 text-emerald-200" />
                                                {formatDate(poster.created_at)}
                                            </div>
                                        </div>

                                        <div className="flex flex-1 flex-col gap-4 p-5">
                                            {poster.image_caption ? (
                                                <p className="text-base font-medium text-emerald-950 line-clamp-3">
                                                    {poster.image_caption}
                                                </p>
                                            ) : (
                                                <p className="text-base italic text-muted-foreground">
                                                    No caption yet – generate
                                                    one from chat.
                                                </p>
                                            )}
                                            <div className="mt-auto flex items-center justify-between border-t border-emerald-50 pt-4">
                                                <div className="flex items-center gap-2">
                                                    {sharePlatforms.map(
                                                        ({
                                                            key,
                                                            label,
                                                            icon: Icon,
                                                            className,
                                                        }) => (
                                                            <button
                                                                key={key}
                                                                onClick={() =>
                                                                    shareToSocialMedia(
                                                                        poster,
                                                                        key
                                                                    )
                                                                }
                                                                className={cn(
                                                                    "flex h-10 w-10 items-center justify-center rounded-full border border-emerald-100/70 text-emerald-600 transition-colors hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2",
                                                                    className
                                                                )}
                                                                aria-label={`Share on ${label}`}
                                                            >
                                                                <Icon className="h-[18px] w-[18px]" />
                                                            </button>
                                                        )
                                                    )}
                                                </div>
                                                <button
                                                    onClick={() =>
                                                        handleCopyCaption(
                                                            poster.image_caption
                                                        )
                                                    }
                                                    className="inline-flex items-center gap-2 rounded-full border border-emerald-100/80 px-4 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2"
                                                >
                                                    <Copy className="h-4 w-4" />{" "}
                                                    Copy caption
                                                </button>
                                            </div>
                                        </div>
                                    </article>
                                ))}
                            </div>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-center gap-4 pt-4">
                                    <Button
                                        variant="outline"
                                        size="icon"
                                        className="rounded-full border-emerald-100 text-emerald-700"
                                        onClick={() =>
                                            setPage((p) => Math.max(1, p - 1))
                                        }
                                        disabled={page === 1}
                                    >
                                        <ChevronLeft className="w-4 h-4" />
                                    </Button>

                                    <span className="text-sm text-muted-foreground">
                                        Page {page} of {totalPages}
                                    </span>

                                    <Button
                                        variant="outline"
                                        size="icon"
                                        className="rounded-full border-emerald-100 text-emerald-700"
                                        onClick={() =>
                                            setPage((p) =>
                                                Math.min(totalPages, p + 1)
                                            )
                                        }
                                        disabled={page === totalPages}
                                    >
                                        <ChevronRight className="w-4 h-4" />
                                    </Button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
