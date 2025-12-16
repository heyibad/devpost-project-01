import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Chat from "./pages/Chat";
import Campaigns from "./pages/Campaigns";
import Payments from "./pages/Payments";
import SalesConnector from "./pages/SalesConnector";
import AccountsConfig from "./pages/AccountsConfig";
import InventoryConfig from "./pages/InventoryConfig";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";
import AuthCallback from "./pages/AuthCallback";
import ProtectedRoute from "./components/ProtectedRoute";
import WaitlistGuard from "./components/WaitlistGuard";
import AdminGuard from "./components/AdminGuard";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import TermsOfService from "./pages/TermsOfService";
import Waitlist from "./pages/Waitlist";
import AdminDashboard from "./pages/AdminDashboard";

const queryClient = new QueryClient();

const App = () => (
    <QueryClientProvider client={queryClient}>
        <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Landing />} />
                    <Route path="/auth/callback" element={<AuthCallback />} />
                    {/* Waitlist page - requires auth but NOT waitlist approval */}
                    <Route
                        path="/waitlist"
                        element={
                            <ProtectedRoute>
                                <Waitlist />
                            </ProtectedRoute>
                        }
                    />
                    {/* Admin Dashboard - requires auth and admin privileges */}
                    <Route
                        path="/admin-view"
                        element={
                            <ProtectedRoute>
                                <AdminGuard>
                                    <AdminDashboard />
                                </AdminGuard>
                            </ProtectedRoute>
                        }
                    />
                    {/* Protected routes that require waitlist approval */}
                    <Route
                        path="/chat"
                        element={
                            <ProtectedRoute>
                                <WaitlistGuard>
                                    <Chat />
                                </WaitlistGuard>
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/chat/:conversationId"
                        element={
                            <ProtectedRoute>
                                <WaitlistGuard>
                                    <Chat />
                                </WaitlistGuard>
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/campaigns"
                        element={
                            <ProtectedRoute>
                                <WaitlistGuard>
                                    <Campaigns />
                                </WaitlistGuard>
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/chat/payments"
                        element={
                            <ProtectedRoute>
                                <WaitlistGuard>
                                    <Payments />
                                </WaitlistGuard>
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/chat/sales"
                        element={
                            <ProtectedRoute>
                                <WaitlistGuard>
                                    <SalesConnector />
                                </WaitlistGuard>
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/chat/accounts"
                        element={
                            <ProtectedRoute>
                                <WaitlistGuard>
                                    <AccountsConfig />
                                </WaitlistGuard>
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/chat/inventory"
                        element={
                            <ProtectedRoute>
                                <WaitlistGuard>
                                    <InventoryConfig />
                                </WaitlistGuard>
                            </ProtectedRoute>
                        }
                    />
                    <Route
                        path="/chat/settings"
                        element={
                            <ProtectedRoute>
                                <WaitlistGuard>
                                    <Settings />
                                </WaitlistGuard>
                            </ProtectedRoute>
                        }
                    />
                    {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                    <Route path="/privacy-policy" element={<PrivacyPolicy />} />
                    <Route path="/terms" element={<TermsOfService />} />
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </BrowserRouter>
        </TooltipProvider>
    </QueryClientProvider>
);

export default App;
