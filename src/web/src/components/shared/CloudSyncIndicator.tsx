'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useCloudSync } from '@/hooks/useCloudSync';
import { Cloud, CloudOff, CloudDrizzle, AlertCircle, Unplug } from 'lucide-react';

export function CloudSyncIndicator() {
    const { status, lastSync } = useCloudSync();
    const [showMenu, setShowMenu] = useState(false);
    const [disconnecting, setDisconnecting] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
                setShowMenu(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const getStatusIcon = () => {
        switch (status) {
            case 'idle':
                return <Cloud className="h-4 w-4 text-green-500" />;
            case 'syncing':
                return <CloudDrizzle className="h-4 w-4 text-blue-500 animate-pulse" />;
            case 'error':
                return <AlertCircle className="h-4 w-4 text-red-500" />;
            case 'offline':
                return <CloudOff className="h-4 w-4 text-gray-500" />;
            default:
                return <Cloud className="h-4 w-4 text-gray-400" />;
        }
    };

    const getStatusText = () => {
        switch (status) {
            case 'idle':
                return 'Synced to Drive';
            case 'syncing':
                return 'Syncing changes...';
            case 'error':
                return 'Sync Error';
            case 'offline':
                return 'Connect Google Drive';
            default:
                return 'Sync Unknown';
        }
    };

    const handleConnect = async () => {
        try {
            const response = await fetch('/api/v1/sync/auth-url');
            if (response.ok) {
                const data = await response.json();
                window.location.href = data.url;
            }
        } catch (error) {
            console.error('Failed to fetch auth URL', error);
        }
    };

    const handleDisconnect = async () => {
        setDisconnecting(true);
        try {
            const response = await fetch('/api/v1/sync/disconnect', { method: 'POST' });
            if (response.ok) {
                setShowMenu(false);
            }
        } catch (error) {
            console.error('Failed to disconnect', error);
        } finally {
            setDisconnecting(false);
        }
    };

    const isConnected = status === 'idle' || status === 'syncing';

    const handleClick = () => {
        if (isConnected) {
            setShowMenu(!showMenu);
        } else {
            handleConnect();
        }
    };

    return (
        <div className="relative" ref={menuRef}>
            <div
                className={`flex items-center space-x-2 px-3 py-1 bg-surface-elevated rounded-md border text-xs transition-colors cursor-pointer ${isConnected ? 'border-green-900/30 hover:bg-green-900/10' : 'border-amber-900/50 hover:bg-amber-900/20'
                    }`}
                title={lastSync ? `Last synced: ${new Date(lastSync).toLocaleTimeString()}` : 'Sync Status'}
                onClick={handleClick}
            >
                {getStatusIcon()}
                <span className="hidden sm:inline">{getStatusText()}</span>
            </div>

            {/* Disconnect dropdown */}
            {showMenu && isConnected && (
                <div className="absolute top-full left-0 mt-1 w-56 bg-gray-900 border border-neutral-700 rounded-lg shadow-xl z-50 overflow-hidden">
                    <div className="px-3 py-2 border-b border-neutral-800">
                        <p className="text-xs text-neutral-400">Google Drive is connected</p>
                        {lastSync && (
                            <p className="text-[10px] text-neutral-500 mt-0.5">
                                Last sync: {new Date(lastSync).toLocaleTimeString()}
                            </p>
                        )}
                    </div>
                    <button
                        onClick={handleDisconnect}
                        disabled={disconnecting}
                        className="flex items-center gap-2 w-full px-3 py-2 text-xs text-red-400 hover:bg-red-950/30 transition-colors disabled:opacity-50"
                    >
                        <Unplug className="h-3.5 w-3.5" />
                        {disconnecting ? 'Disconnecting...' : 'Disconnect Google Drive'}
                    </button>
                </div>
            )}
        </div>
    );
}
