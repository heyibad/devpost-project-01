import { ReactNode, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { authApi } from "@/lib/api";

interface ProtectedRouteProps {
    children: ReactNode;
}

/**
 * Protected route wrapper that checks authentication.
 * If user is not authenticated, redirects to landing page.
 * Also validates the token with the backend.
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(
        null
    );

    useEffect(() => {
        const checkAuth = async () => {
            const token = localStorage.getItem("access_token");

            if (!token) {
                setIsAuthenticated(false);
                return;
            }

            try {
                // Verify token with backend
                await authApi.getCurrentUser();
                setIsAuthenticated(true);
            } catch (error) {
                // Token is invalid or expired
                console.error("Authentication failed:", error);
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                setIsAuthenticated(false);
            }
        };

        checkAuth();
    }, []);

    // Show loading state while checking authentication
    if (isAuthenticated === null) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-background">
                <div className="text-center space-y-4">
                    <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto" />
                    <p className="text-muted-foreground">
                        Checking authentication...
                    </p>
                </div>
            </div>
        );
    }

    // Redirect to landing if not authenticated
    if (!isAuthenticated) {
        return <Navigate to="/" replace />;
    }

    // Render protected content
    return <>{children}</>;
}
