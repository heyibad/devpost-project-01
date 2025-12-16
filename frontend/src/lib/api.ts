import axios, {
    AxiosError,
    AxiosRequestHeaders,
    AxiosResponse,
    InternalAxiosRequestConfig,
} from "axios";

interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
    _retry?: boolean;
}

interface FailedRequest {
    resolve: (value: AxiosResponse) => void;
    reject: (reason?: unknown) => void;
    config: RetryableRequestConfig;
}

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "https://api.example.com";

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

const failedQueue: FailedRequest[] = [];
let isRefreshing = false;

const saveTokens = (tokens: TokenResponse) => {
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    api.defaults.headers.common.Authorization = `Bearer ${tokens.access_token}`;
};

const processQueue = (error: unknown | null, token?: string) => {
    while (failedQueue.length > 0) {
        const { resolve, reject, config } = failedQueue.shift()!;

        if (error) {
            reject(error);
            continue;
        }

        if (token) {
            config.headers = config.headers ?? ({} as AxiosRequestHeaders);
            config.headers.Authorization = `Bearer ${token}`;
        }

        api(config).then(resolve).catch(reject);
    }
};

// Add token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = (error.config || {}) as RetryableRequestConfig;

        if (
            error.response?.status === 401 &&
            !originalRequest?._retry &&
            !originalRequest.url?.includes("/auth/login") &&
            !originalRequest.url?.includes("/auth/register") &&
            !originalRequest.url?.includes("/auth/refresh")
        ) {
            const refreshToken = localStorage.getItem("refresh_token");

            if (!refreshToken) {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                delete api.defaults.headers.common.Authorization;
                return Promise.reject(error);
            }

            if (isRefreshing) {
                return new Promise((resolve, reject) => {
                    originalRequest._retry = true;
                    failedQueue.push({
                        resolve,
                        reject,
                        config: originalRequest,
                    });
                });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                const response = await api.post<TokenResponse>(
                    "/api/v1/auth/refresh",
                    { refresh_token: refreshToken }
                );

                saveTokens(response.data);

                processQueue(null, response.data.access_token);

                originalRequest.headers =
                    originalRequest.headers ?? ({} as AxiosRequestHeaders);
                originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;

                return api(originalRequest);
            } catch (refreshError) {
                processQueue(refreshError);
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                delete api.defaults.headers.common.Authorization;
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

// Auth APIs
export const authApi = {
    register: async (email: string, password: string, name?: string) => {
        const response = await api.post("/api/v1/auth/register", {
            email,
            password,
            name,
        });
        return response.data;
    },

    login: async (email: string, password: string) => {
        const response = await api.post<TokenResponse>("/api/v1/auth/login", {
            email,
            password,
        });
        saveTokens(response.data);
        return response.data;
    },

    googleAuthUrl: async () => {
        const response = await api.get("/api/v1/oauth/google/auth-url");
        return response.data;
    },

    googleTokenExchange: async (code: string) => {
        const response = await api.post<TokenResponse>(
            "/api/v1/oauth/google/token",
            { code }
        );
        saveTokens(response.data);
        return response.data;
    },

    logout: async () => {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
            await api.post("/api/v1/auth/logout", {
                refresh_token: refreshToken,
            });
        }
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        delete api.defaults.headers.common.Authorization;
    },

    getCurrentUser: async () => {
        const response = await api.get("/api/v1/auth/me");
        return response.data;
    },

    refreshAccessToken: async () => {
        const refreshToken = localStorage.getItem("refresh_token");

        if (!refreshToken) {
            throw new Error("No refresh token available");
        }

        const response = await api.post<TokenResponse>("/api/v1/auth/refresh", {
            refresh_token: refreshToken,
        });

        saveTokens(response.data);
        return response.data;
    },

    // Public endpoint - no auth required
    getWaitlistStatus: async () => {
        const response = await api.get<{ waitlist_enabled: boolean }>(
            "/api/v1/auth/waitlist-status"
        );
        return response.data;
    },
};

// Chat APIs
export interface ChatMessage {
    role: "user" | "assistant" | "system";
    content: string;
}

export interface StreamSnapshot {
    conversation: {
        id: string;
        title: string | null;
        model: string;
        user_id: string;
        created_at: string;
    };
    request_message: {
        id: string;
        conversation_id: string;
        role: string;
        content: string;
        status: string;
        created_at: string;
    };
    response_message: {
        id: string;
        conversation_id: string;
        role: string;
        content: string;
        status: string;
        created_at: string;
    };
}

export interface ConversationListItem {
    id: string;
    title: string;
    created_at: string;
    last_message_at: string;
    last_message_preview: string;
    message_count: number;
}

export interface ConversationDetail {
    id: string;
    title: string;
    created_at: string;
    last_message_at: string;
    messages: Array<{
        id: string;
        role: string;
        content: string;
        created_at: string;
        status: string;
    }>;
    message_count: number;
}

export const chatApi = {
    stream: async (
        messages: ChatMessage[],
        conversationId: string | null,
        onChunk: (chunk: string) => void,
        onSnapshot?: (snapshot: StreamSnapshot) => void
    ) => {
        const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            },
            body: JSON.stringify({
                messages,
                conversation_id: conversationId,
            }),
        });

        if (!response.ok) {
            throw new Error("Failed to stream chat");
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No reader available");

        // ULTRA-OPTIMIZED: Use Uint8Array decoder for better performance
        const decoder = new TextDecoder();
        let buffer = "";
        let currentEvent = "";

        // ULTRA-OPTIMIZED: Pre-allocate common strings to reduce allocations
        const EVENT_PREFIX = "event: ";
        const DATA_PREFIX = "data: ";
        const SNAPSHOT_EVENT = "snapshot";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            // ULTRA-OPTIMIZED: Decode immediately and process
            buffer += decoder.decode(value, { stream: true });

            // ULTRA-OPTIMIZED: Fast path for single complete events
            let nlPos = buffer.indexOf("\n\n");

            while (nlPos !== -1) {
                const event = buffer.slice(0, nlPos);
                buffer = buffer.slice(nlPos + 2);

                // Process this complete event
                const lines = event.split("\n");

                for (const line of lines) {
                    if (!line) continue;

                    // ULTRA-OPTIMIZED: Fast prefix checks
                    if (
                        line.charCodeAt(0) === 101 &&
                        line.startsWith(EVENT_PREFIX)
                    ) {
                        // 'e' = 101
                        currentEvent = line.slice(EVENT_PREFIX.length);
                        continue;
                    }

                    if (
                        line.charCodeAt(0) === 100 &&
                        line.startsWith(DATA_PREFIX)
                    ) {
                        // 'd' = 100
                        const data = line.slice(DATA_PREFIX.length);
                        if (!data || data === "[DONE]") continue;

                        try {
                            const parsed = JSON.parse(data);

                            // ULTRA-OPTIMIZED: Fast path for snapshot
                            if (currentEvent === SNAPSHOT_EVENT) {
                                if (onSnapshot && parsed.conversation) {
                                    onSnapshot(parsed as StreamSnapshot);
                                }
                                currentEvent = "";
                                continue;
                            }

                            // ULTRA-OPTIMIZED: Fast path for delta chunks (most common)
                            if (parsed.delta) {
                                onChunk(parsed.delta);
                                continue;
                            }

                            // Fallback paths (rare)
                            if (parsed.response_message?.content) {
                                onChunk(parsed.response_message.content);
                            } else if (parsed.choices?.[0]?.delta?.content) {
                                onChunk(parsed.choices[0].delta.content);
                            }
                        } catch (e) {
                            // Silently ignore parse errors for incomplete chunks
                        }
                    }
                }

                nlPos = buffer.indexOf("\n\n");
            }
        }
    },

    getConversations: async (limit: number = 20, offset: number = 0) => {
        const response = await api.get<{
            conversations: ConversationListItem[];
            total: number;
            limit: number;
            offset: number;
        }>(`/api/v1/chat/conversations?limit=${limit}&offset=${offset}`);
        return response.data;
    },

    getConversation: async (conversationId: string) => {
        const response = await api.get<ConversationDetail>(
            `/api/v1/chat/conversations/${conversationId}`
        );
        return response.data;
    },
};

// Google Sheets API Types
export interface OrderItem {
    id: string;
    date: string;
    customer: string;
    amount: number;
    amount_display: string;
    method: string;
    status: string;
}

export interface OrdersStats {
    total_revenue: number;
    completed_count: number;
    pending_count: number;
}

export interface OrdersDataResponse {
    orders: OrderItem[];
    stats: OrdersStats;
    last_synced_at: string;
}

export interface GoogleSheetsConnectionStatus {
    is_connected: boolean;
    refresh_token: string | null;
    token_expires_at: string | null;
    is_token_expired: boolean;
    inventory_workbook_id: string | null;
    inventory_worksheet_name: string | null;
    orders_workbook_id: string | null;
    orders_worksheet_name: string | null;
    last_synced_at: string | null;
}

// Google Sheets APIs
export const googleSheetsApi = {
    getConnectionStatus: async () => {
        const response = await api.get<GoogleSheetsConnectionStatus>(
            "/api/v1/google-sheets/status"
        );
        return response.data;
    },

    getOrdersData: async () => {
        const response = await api.get<OrdersDataResponse>(
            "/api/v1/google-sheets/orders"
        );
        return response.data;
    },
};

// Waitlist Types
export interface WaitlistStatus {
    is_on_waitlist: boolean;
    is_approved: boolean;
    position: number | null;
    message: string | null;
    use_case: string | null;
    business_type: string | null;
    submitted_at: string | null;
    approved_at: string | null;
}

export interface WaitlistSubmitRequest {
    message?: string;
    use_case?: string;
    business_type?: string;
}

export interface WaitlistSubmitResponse {
    success: boolean;
    message: string;
    waitlist_status: WaitlistStatus;
}

export interface WaitlistAccessResponse {
    has_access: boolean;
    is_approved: boolean;
}

// Waitlist APIs
export const waitlistApi = {
    getStatus: async () => {
        const response = await api.get<WaitlistStatus>(
            "/api/v1/waitlist/status"
        );
        return response.data;
    },

    submit: async (data: WaitlistSubmitRequest) => {
        const response = await api.post<WaitlistSubmitResponse>(
            "/api/v1/waitlist/submit",
            data
        );
        return response.data;
    },

    checkAccess: async () => {
        const response = await api.get<WaitlistAccessResponse>(
            "/api/v1/waitlist/check-access"
        );
        return response.data;
    },
};

// ============================================================================
// Admin Types
// ============================================================================

export interface DashboardStats {
    total_users: number;
    approved_users: number;
    pending_waitlist: number;
    total_conversations: number;
    total_messages: number;
    users_today: number;
    users_this_week: number;
    users_this_month: number;
}

export interface WaitlistUser {
    id: string;
    tenant_id: string;
    email: string;
    name: string | null;
    is_approved: boolean;
    message: string | null;
    use_case: string | null;
    business_type: string | null;
    submitted_at: string;
    approved_at: string | null;
    oauth_provider: string | null;
    avatar_url: string | null;
}

export interface WaitlistListResponse {
    items: WaitlistUser[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface AdminUser {
    id: string;
    email: string;
    name: string | null;
    is_active: boolean;
    is_admin: boolean;
    is_waitlist_approved: boolean;
    oauth_provider: string | null;
    avatar_url: string | null;
    subscription_plan: string | null;
    created_at: string;
    conversation_count: number;
    message_count: number;
}

export interface UserListResponse {
    items: AdminUser[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface ApproveResponse {
    success: boolean;
    message: string;
    email_sent: boolean;
}

export interface AdminCheckResponse {
    is_admin: boolean;
    email: string;
    name: string | null;
}

// ============================================================================
// Admin APIs
// ============================================================================

export const adminApi = {
    checkAccess: async () => {
        const response = await api.get<AdminCheckResponse>(
            "/api/v1/admin/check"
        );
        return response.data;
    },

    getStats: async () => {
        const response = await api.get<DashboardStats>("/api/v1/admin/stats");
        return response.data;
    },

    getWaitlist: async (params?: {
        page?: number;
        page_size?: number;
        status_filter?: "pending" | "approved" | "all";
        search?: string;
    }) => {
        const response = await api.get<WaitlistListResponse>(
            "/api/v1/admin/waitlist",
            { params }
        );
        return response.data;
    },

    approveUser: async (waitlistId: string, sendEmail: boolean = true) => {
        const response = await api.post<ApproveResponse>(
            `/api/v1/admin/waitlist/${waitlistId}/approve`,
            { send_email: sendEmail }
        );
        return response.data;
    },

    rejectUser: async (waitlistId: string) => {
        const response = await api.post<ApproveResponse>(
            `/api/v1/admin/waitlist/${waitlistId}/reject`
        );
        return response.data;
    },

    getUsers: async (params?: {
        page?: number;
        page_size?: number;
        search?: string;
        admin_only?: boolean;
    }) => {
        const response = await api.get<UserListResponse>(
            "/api/v1/admin/users",
            { params }
        );
        return response.data;
    },

    updateUser: async (
        userId: string,
        data: {
            is_admin?: boolean;
            is_active?: boolean;
            subscription_plan?: string;
        }
    ) => {
        const response = await api.patch<AdminUser>(
            `/api/v1/admin/users/${userId}`,
            data
        );
        return response.data;
    },

    makeAdmin: async (userId: string) => {
        const response = await api.post<ApproveResponse>(
            `/api/v1/admin/users/${userId}/make-admin`
        );
        return response.data;
    },

    removeAdmin: async (userId: string) => {
        const response = await api.post<ApproveResponse>(
            `/api/v1/admin/users/${userId}/remove-admin`
        );
        return response.data;
    },

    // Waitlist Settings
    getWaitlistSettings: async () => {
        const response = await api.get<{
            waitlist_enabled: boolean;
            updated_at: string;
            updated_by: string | null;
        }>("/api/v1/admin/settings/waitlist");
        return response.data;
    },

    updateWaitlistSettings: async (waitlistEnabled: boolean) => {
        const response = await api.put<{
            waitlist_enabled: boolean;
            updated_at: string;
            updated_by: string | null;
        }>("/api/v1/admin/settings/waitlist", {
            waitlist_enabled: waitlistEnabled,
        });
        return response.data;
    },
};
