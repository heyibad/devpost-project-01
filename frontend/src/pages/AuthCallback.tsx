import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";

/**
 * OAuth callback handler page.
 * Parses access_token and refresh_token from URL params,
 * stores them in localStorage, and redirects to /chat.
 */
export default function AuthCallback() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    useEffect(() => {
        const accessToken = searchParams.get("access_token");
        const refreshToken = searchParams.get("refresh_token");
        const error = searchParams.get("error");

        if (error) {
            // OAuth error occurred
            console.error("OAuth error:", decodeURIComponent(error));
            navigate("/", { replace: true });
            return;
        }

        if (accessToken && refreshToken) {
            // Store tokens in localStorage
            localStorage.setItem("access_token", accessToken);
            localStorage.setItem("refresh_token", refreshToken);

            // Redirect to chat page
            navigate("/chat", { replace: true });
        } else {
            // If tokens are missing, redirect to landing page
            console.error("Missing tokens in OAuth callback");
            navigate("/", { replace: true });
        }
    }, [searchParams, navigate]);

    return (
        <div className="flex items-center justify-center min-h-screen bg-background">
            <div className="text-center space-y-4">
                <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto" />
                <p className="text-muted-foreground">
                    Completing authentication...
                </p>
            </div>
        </div>
    );
}
