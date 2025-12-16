import React from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

export default function PrivacyPolicy() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-background selection:bg-primary/20 p-8">
            <div className="container mx-auto max-w-4xl glass p-8 rounded-2xl">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold">
                            Privacy Policy — Sahulat AI
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            Effective Date: 25 November 2025
                        </p>
                    </div>
                    <div className="hidden sm:block">
                        <Button variant="ghost" onClick={() => navigate(-1)}>
                            Back
                        </Button>
                    </div>
                </div>

                <article className="prose prose-slate mt-6 max-w-none">
                    <p>
                        Welcome to <strong>Sahulat AI</strong>, a multi-tenant,
                        agentic AI platform designed to help small and medium
                        businesses manage sales, marketing, accounting,
                        inventory, payments, and customer support using
                        autonomous AI agents. This Privacy Policy explains how
                        we collect, use, store, and protect your information
                        when you use Sahulat AI.
                    </p>

                    <h2>1. Information We Collect</h2>

                    <h3>1.1 User-Provided Information</h3>
                    <ul>
                        <li>
                            Account information (name, email, business details)
                        </li>
                        <li>
                            WhatsApp Business number (when connected via
                            Evolution API)
                        </li>
                        <li>Google account information during OAuth login</li>
                        <li>
                            QuickBooks account details (OAuth connection only)
                        </li>
                    </ul>

                    <h3>1.2 Business Data</h3>
                    <p>
                        From your connected tools (based on your permissions):
                    </p>
                    <ul>
                        <li>WhatsApp conversations</li>
                        <li>
                            Orders, customers, product sheets (Google Sheets)
                        </li>
                        <li>
                            Accounting data such as invoices, payments, bills
                            (QuickBooks)
                        </li>
                        <li>Inventory records</li>
                        <li>Marketing content &amp; email campaigns</li>
                    </ul>
                    <p>
                        This data is{" "}
                        <strong>never shared between tenants</strong> thanks to
                        multi-tenant isolation in the platform architecture.
                    </p>

                    <h2>2. How We Use Your Information</h2>
                    <p>Sahulat AI uses your data to:</p>
                    <ul>
                        <li>Enable AI agents to perform business tasks</li>
                        <li>Manage WhatsApp customer support</li>
                        <li>Generate email marketing, ads, and posters</li>
                        <li>Manage inventory, products, orders</li>
                        <li>Perform accounting operations (via QuickBooks)</li>
                        <li>
                            Improve agent reasoning and contextual responses
                        </li>
                        <li>
                            Provide secure access through OAuth 2.0 standards
                        </li>
                    </ul>

                    <h2>3. Data Protection &amp; Security</h2>
                    <p>We implement:</p>
                    <ul>
                        <li>
                            <strong>OAuth 2.0</strong> per-user authentication
                        </li>
                        <li>
                            <strong>Multi-tenant isolation</strong> (each
                            business fully separated)
                        </li>
                        <li>
                            <strong>Encrypted storage</strong> for conversation
                            and business data
                        </li>
                        <li>
                            <strong>Stateless tool execution</strong> ensuring
                            correct user context per call
                        </li>
                    </ul>
                    <p>Your data is never used to train external AI models.</p>

                    <h2>4. Third-Party Services</h2>
                    <p>
                        We integrate with external services including but not
                        limited to:
                    </p>
                    <ul>
                        <li>WhatsApp Evolution API</li>
                        <li>Google Sheets API</li>
                        <li>QuickBooks Online API</li>
                        <li>ImageKit for CDN</li>
                        <li>
                            OpenAI, Google Gemini, and GPT models for LLM
                            features
                        </li>
                    </ul>

                    <h2>5. Your Rights</h2>
                    <ul>
                        <li>Request data deletion</li>
                        <li>
                            Disconnect QuickBooks / Google / WhatsApp at any
                            time
                        </li>
                        <li>Export your conversations and business data</li>
                    </ul>

                    <h2>6. Data Retention</h2>
                    <p>
                        We retain your data only while your account is active.
                        If you close your account, we delete your data within{" "}
                        <strong>30 days</strong>.
                    </p>

                    <h2>7. Contact Us</h2>
                    <p>
                        For privacy concerns, contact us at{" "}
                        <a href="mailto:connect.sahulatai@gmail.com">
                            connect.sahulatai@gmail.com
                        </a>
                        or visit{" "}
                        <a href="https://sahulatai.app">
                            https://sahulatai.app
                        </a>
                        .
                    </p>
                </article>
            </div>
        </div>
    );
}
