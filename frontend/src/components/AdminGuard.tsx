import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { adminApi } from "@/lib/api";

interface AdminGuardProps {
    children: React.ReactNode;
}

const AdminGuard = ({ children }: AdminGuardProps) => {
    const [isAdmin, setIsAdmin] = useState<boolean | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const checkAdminAccess = async () => {
            try {
                const response = await adminApi.checkAccess();
                setIsAdmin(response.is_admin);
            } catch (error) {
                // If error (e.g., 403 Forbidden), user is not admin
                console.error("Admin access check failed:", error);
                setIsAdmin(false);
            } finally {
                setIsLoading(false);
            }
        };

        checkAdminAccess();
    }, []);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-slate-400 text-sm">
                        Checking admin access...
                    </p>
                </div>
            </div>
        );
    }

    if (!isAdmin) {
        return <Navigate to="/chat" replace />;
    }

    return <>{children}</>;
};

export default AdminGuard;
