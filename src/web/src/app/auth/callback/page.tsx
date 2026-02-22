'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';

function AuthCallbackInner() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const code = searchParams.get('code');
        if (!code) {
            setStatus('error');
            setError('No authorization code found in URL');
            return;
        }

        const exchangeCode = async () => {
            try {
                const response = await fetch('/api/v1/sync/auth', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ auth_code: code }),
                });

                if (response.ok) {
                    setStatus('success');
                    setTimeout(() => router.push('/dashboard'), 2000);
                } else {
                    const data = await response.json();
                    throw new Error(data.detail || 'Failed to exchange code for tokens');
                }
            } catch (err: any) {
                setStatus('error');
                setError(err.message);
            }
        };

        exchangeCode();
    }, [searchParams, router]);

    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
            {status === 'loading' && (
                <>
                    <Loader2 className="h-12 w-12 text-indigo-500 animate-spin" />
                    <h1 className="text-xl font-medium text-neutral-200">Connecting to Google Drive...</h1>
                    <p className="text-neutral-500">Please wait while we set up your secure sync.</p>
                </>
            )}

            {status === 'success' && (
                <>
                    <CheckCircle className="h-12 w-12 text-green-500" />
                    <h1 className="text-xl font-medium text-neutral-200">Connected Successfully!</h1>
                    <p className="text-neutral-500">Redirecting you back to the dashboard...</p>
                </>
            )}

            {status === 'error' && (
                <>
                    <XCircle className="h-12 w-12 text-red-500" />
                    <h1 className="text-xl font-medium text-neutral-200">Connection Failed</h1>
                    <p className="text-red-400 text-sm max-w-md text-center">{error}</p>
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded-md transition-colors"
                    >
                        Go back to Dashboard
                    </button>
                </>
            )}
        </div>
    );
}

export default function AuthCallback() {
    return (
        <Suspense fallback={
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
                <Loader2 className="h-12 w-12 text-indigo-500 animate-spin" />
                <h1 className="text-xl font-medium text-neutral-200">Loading...</h1>
            </div>
        }>
            <AuthCallbackInner />
        </Suspense>
    );
}
