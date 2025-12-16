import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export interface PosterGeneration {
    id: string;
    tenant_id: string;
    image_url: string;
    image_caption: string | null;
    created_at: string;
}

export interface PosterListResponse {
    items: PosterGeneration[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export const posterApi = {
    getPosters: async (
        page: number = 1,
        pageSize: number = 20
    ): Promise<PosterListResponse> => {
        const response = await api.get<PosterListResponse>(`/api/v1/posters`, {
            params: { page, page_size: pageSize },
        });
        return response.data;
    },

    getPoster: async (posterId: string): Promise<PosterGeneration> => {
        const response = await api.get<PosterGeneration>(
            `/api/v1/posters/${posterId}`
        );
        return response.data;
    },
};

export function usePosters(page: number = 1, pageSize: number = 20) {
    const [posters, setPosters] = useState<PosterGeneration[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [totalPages, setTotalPages] = useState(0);
    const [total, setTotal] = useState(0);

    useEffect(() => {
        const fetchPosters = async () => {
            try {
                setLoading(true);
                setError(null);
                const data = await posterApi.getPosters(page, pageSize);
                setPosters(data.items);
                setTotalPages(data.total_pages);
                setTotal(data.total);
            } catch (err) {
                const errorMessage =
                    err instanceof Error
                        ? err.message
                        : "Failed to load posters";
                setError(errorMessage);
                console.error("Error fetching posters:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchPosters();
    }, [page, pageSize]);

    return { posters, loading, error, totalPages, total };
}
