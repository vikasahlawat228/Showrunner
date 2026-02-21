"use client";

import React, { ErrorInfo, ReactNode } from "react";
import Link from "next/link";

// Using a simple inline SVG since lucide-react might not import well in class components without extra config in some setups
const AlertTriangleIcon = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="48"
        height="48"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-red-500 mb-4"
    >
        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
        <path d="M12 9v4" />
        <path d="M12 17h.01" />
    </svg>
);

interface Props {
    children?: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        // Update state so the next render will show the fallback UI.
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    private handleTryAgain = () => {
        this.setState({ hasError: false, error: null });
    };

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="min-h-screen w-full flex items-center justify-center bg-gray-950 p-4">
                    <div className="max-w-md w-full bg-gray-900 border border-gray-800 rounded-xl shadow-2xl p-8 flex flex-col items-center text-center">
                        <AlertTriangleIcon />
                        <h1 className="text-xl font-bold text-gray-100 mb-2">
                            Something went wrong
                        </h1>
                        <p className="text-gray-400 text-sm mb-6">
                            An unexpected error occurred in this component.
                        </p>

                        {this.state.error && (
                            <div className="w-full bg-gray-950 border border-gray-800 rounded-lg p-4 text-xs font-mono text-red-400 text-left mb-6 overflow-hidden text-ellipsis whitespace-nowrap">
                                {this.state.error.message}
                            </div>
                        )}

                        <div className="flex flex-col gap-3 w-full">
                            <button
                                onClick={this.handleTryAgain}
                                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
                            >
                                Try Again
                            </button>
                            <Link
                                href="/dashboard"
                                onClick={this.handleTryAgain}
                                className="text-gray-400 hover:text-gray-200 text-sm transition-colors py-2"
                            >
                                Go to Dashboard
                            </Link>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
