import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { waitlistApi, authApi } from "@/lib/api";

interface WaitlistGuardProps {
    children: React.ReactNode;
}

const WaitlistGuard = ({ children }: WaitlistGuardProps) => {
    const [hasAccess, setHasAccess] = useState<boolean | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const checkAccess = async () => {
            try {
                // First check if waitlist feature is enabled globally
                const waitlistStatus = await authApi.getWaitlistStatus();

                // If waitlist is disabled, all authenticated users have access
                if (!waitlistStatus.waitlist_enabled) {
                    setHasAccess(true);
                    return;
                }

                // Waitlist is enabled, check user's individual access
                const response = await waitlistApi.checkAccess();
                setHasAccess(response.has_access);
            } catch (error) {
                // If error (e.g., API failure), assume no access
                console.error("Error checking waitlist access:", error);
                setHasAccess(false);
            } finally {
                setIsLoading(false);
            }
        };

        checkAccess();
    }, []);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-slate-400 text-sm">Checking access...</p>
                </div>
            </div>
        );
    }

    if (!hasAccess) {
        return <Navigate to="/waitlist" replace />;
    }

    return <>{children}</>;
};

export default WaitlistGuard;
