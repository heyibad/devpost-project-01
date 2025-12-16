import React from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

export default function TermsOfService() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-background selection:bg-primary/20 p-8">
            <div className="container mx-auto max-w-4xl glass p-8 rounded-2xl">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold">
                            Terms of Service — Sahulat AI
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
                        Welcome to <strong>Sahulat AI</strong>, a multi-agent
                        business automation platform. By using Sahulat AI, you
                        agree to the terms below.
                    </p>

                    <h2>1. Service Description</h2>
                    <p>Sahulat AI provides:</p>
                    <ul>
                        <li>
                            AI agents for sales, customer support, and WhatsApp
                            automation
                        </li>
                        <li>
                            Marketing tools such as email campaigns &amp; poster
                            generation
                        </li>
                        <li>Inventory and order management</li>
                        <li>
                            Accounting automation through QuickBooks
                            integrations
                        </li>
                        <li>Payment management &amp; custom payment links</li>
                    </ul>

                    <h2>2. User Responsibilities</h2>
                    <ul>
                        <li>Provide accurate business information</li>
                        <li>
                            Use Sahulat AI only for lawful business purposes
                        </li>
                        <li>
                            Maintain control over connected accounts (WhatsApp,
                            QuickBooks, Google, etc.)
                        </li>
                        <li>
                            Not misuse AI agents or automate harmful content
                        </li>
                    </ul>

                    <h2>3. Account &amp; Access</h2>
                    <p>
                        You are responsible for securing your login credentials,
                        managing team access in your tenant, and revoking OAuth
                        access when no longer needed. We may suspend accounts
                        that violate security or legal policies.
                    </p>

                    <h2>4. Data Usage &amp; Permissions</h2>
                    <p>
                        By connecting external services, you grant Sahulat AI
                        permission to:
                    </p>
                    <ul>
                        <li>Read and process your WhatsApp chat data</li>
                        <li>Read and write Google Sheets data</li>
                        <li>
                            Read/write QuickBooks data (invoices, bills,
                            payments, vendors, customers)
                        </li>
                        <li>Generate marketing content using LLMs</li>
                    </ul>
                    <p>
                        We never sell your data or share tenant data with other
                        tenants.
                    </p>

                    <h2>5. AI Output Responsibility</h2>
                    <p>
                        AI-generated results may contain errors. You are
                        responsible for verifying accounting, marketing, or
                        operational decisions suggested by AI. Sahulat AI is not
                        liable for financial losses due to incorrect AI outputs.
                    </p>

                    <h2>6. Prohibited Use</h2>
                    <p>You may NOT use Sahulat AI for:</p>
                    <ul>
                        <li>Fraud, spam, or harmful automation</li>
                        <li>Illegal financial manipulation</li>
                        <li>Spreading misinformation</li>
                        <li>
                            Automating harassment or scam messages on WhatsApp
                        </li>
                    </ul>

                    <h2>7. Service Availability</h2>
                    <p>
                        We rely on third-party services (WhatsApp Evolution API,
                        Google APIs, QuickBooks API, etc.). Downtime in these
                        external services may affect Sahulat AI operations.
                    </p>

                    <h2>8. Limitation of Liability</h2>
                    <p>
                        Sahulat AI is provided <em>“as-is”</em>, without
                        warranties. We are not liable for loss of profits,
                        business data loss, or errors caused by external APIs.
                    </p>

                    <h2>9. Termination</h2>
                    <p>
                        You may delete your account anytime. We may terminate
                        access for policy violations, abuse of AI agents, fraud
                        or harmful activity.
                    </p>

                    <h2>10. Contact</h2>
                    <p>
                        For questions about these terms, contact{" "}
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
