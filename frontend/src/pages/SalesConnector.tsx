import { useState, useEffect, useRef } from 'react';
import ChatSidebar from '@/components/ChatSidebar';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { MessageCircle, ExternalLink, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

function SalesConnector() {
  const [connectionState, setConnectionState] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCheckingStatus, setIsCheckingStatus] = useState<boolean>(true);
  const [isDisconnecting, setIsDisconnecting] = useState<boolean>(false);
  const [showDisconnectDialog, setShowDisconnectDialog] = useState<boolean>(false);
  
  // Use refs to manage a single polling loop that won't overlap
  const pollingActiveRef = useRef<boolean>(false);
  const pollingTaskRef = useRef<Promise<void> | null>(null);

  // Check initial connection status by calling /instance_connect on mount
  const checkInitialConnectionStatus = async () => {
    try {
      setIsCheckingStatus(true);
      const { data } = await api.get('/api/v1/instance_connect');

      console.debug('[Init] instance_connect response:', data);

      // Check if connected
      const isConnected =
        data?.is_connected === true ||
        data?.state === 'open' ||
        data?.state === 'connected';

      if (isConnected) {
        console.log('[Init] WhatsApp is already connected');
        setConnectionState('connected');
      } else if (data?.instance_exists === false || data?.state === 'not_found') {
        console.log('[Init] WhatsApp instance does not exist');
        setConnectionState('disconnected');
      } else {
        console.log('[Init] WhatsApp is not connected');
        setConnectionState('disconnected');
      }
    } catch (err) {
      console.error('[Init] Error checking initial connection status:', err);
      // Default to disconnected on error - don't show error message on initial load
      // User can try to connect manually if needed
      setConnectionState('disconnected');
    } finally {
      setIsCheckingStatus(false);
    }
  };

  const startConnection = async () => {
    try {
      // Prevent starting if already connecting/connected
      if (connectionState === 'connecting' || connectionState === 'connected') return;

      setConnectionState('connecting');
      setError(null);

      // Get QR code
      const { data } = await api.get('/api/v1/instance_create');

      // Log full response for debugging in browser console
      // (helps when Evolution API returns a different key or nested object)
      console.debug('[QR] instance_create response:', data);

      // Accept several possible response shapes (qrcode, qrCode, nested data)
      const qr = (data && (data.qrcode || data.qrCode)) || (data && data.data && (data.data.qrcode || data.data.qrCode)) || null;

      if (qr) {
        setQrCode(qr);
        // Start a single polling loop (non-overlapping)
        if (!pollingActiveRef.current) {
          pollingActiveRef.current = true;
          console.debug('[Poll] Starting instance_connect polling loop');
          // create a background async loop
          const loop = (async () => {
            while (pollingActiveRef.current) {
              try {
                console.debug('[Poll] Checking connection status...');
                await checkConnectionStatus();
                if (!pollingActiveRef.current) {
                  console.debug('[Poll] Loop stopped, exiting');
                  break;
                }
                console.debug('[Poll] Waiting 3s before next check');
                await new Promise((res) => setTimeout(res, 3000));
              } catch (e) {
                // swallow — checkConnectionStatus logs errors
                console.error('[Poll] Error in check:', e);
              }
            }
            console.debug('[Poll] Background loop ended');
          })();
          pollingTaskRef.current = loop;
        }
      } else {
        // No QR code received - stop any polling and reset state
        pollingActiveRef.current = false;
        pollingTaskRef.current = null;
        setQrCode(null);
        setConnectionState('disconnected');
        setError('Unable to generate QR code. Please try again.');
        console.error('No QR code in instance_create response:', data);
      }
    } catch (err: any) {
      console.error('Connection error:', err);
      
      // Stop any polling that might have started
      pollingActiveRef.current = false;
      pollingTaskRef.current = null;
      
      // Clear QR code if any
      setQrCode(null);
      
      // Extract user-friendly error message
      let userMessage = 'Unable to connect to WhatsApp. ';
      
      if (err?.response?.data?.detail) {
        // Backend returned a specific error message
        userMessage = err.response.data.detail;
      } else if (err?.code === 'ERR_NETWORK' || err?.message?.includes('Network Error')) {
        userMessage = 'Network connection failed. Please check your internet connection and try again.';
      } else if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')) {
        userMessage = 'Connection timed out. Please try again.';
      } else if (err?.response?.status === 503) {
        userMessage = 'WhatsApp service is temporarily unavailable. Please try again in a moment.';
      } else if (err?.response?.status === 500) {
        userMessage = 'Server error occurred. Please try again.';
      } else {
        userMessage = 'An unexpected error occurred. Please try again.';
      }
      
      setError(userMessage);
      
      // CRITICAL: Reset to disconnected state so button becomes clickable again
      setConnectionState('disconnected');
    }
  };

  const checkConnectionStatus = async () => {
    try {
      const { data } = await api.get('/api/v1/instance_connect');

      console.debug('[Poll] instance_connect response:', data);
      console.debug('[Poll] Connection state:', data?.state);

      // Check if instance doesn't exist (has been deleted)
      if (data?.instance_exists === false || data?.state === 'not_found') {
        console.log('[Poll] Instance does not exist - disconnected');
        setConnectionState('disconnected');
        setQrCode(null);
        // Stop polling
        pollingActiveRef.current = false;
        pollingTaskRef.current = null;
        return;
      }

      // Check if connected
      const isConnected =
        data?.is_connected === true ||
        data?.state === 'open' ||
        data?.state === 'connected';

      if (isConnected) {
        console.log('[Poll] WhatsApp successfully connected!');
        setConnectionState('connected');
        setQrCode(null);
        // Stop the polling loop
        console.debug('[Poll] Stopping instance_connect polling loop (connected)');
        pollingActiveRef.current = false;
        pollingTaskRef.current = null;
        return;
      }

      // Show current state in UI while connecting
      const currentState = data?.state;
      if (currentState && currentState !== 'connected') {
        console.debug(`[Poll] Still connecting... Current state: ${currentState}`);
      }
    } catch (err: any) {
      // On error, keep current state but DON'T show error to user during polling
      // Only log to console for debugging
      console.error('[Poll] Check error:', err);
      
      // Only show error if it's been failing for a while (not a transient network issue)
      // This prevents annoying error messages during temporary connection issues
    }
  };

  const disconnectWhatsApp = async () => {
    try {
      setIsDisconnecting(true);
      setError(null);
      console.debug('[Disconnect] Disconnecting WhatsApp...');
      
      // Call disconnect endpoint to delete the instance
      const { data } = await api.post('/api/v1/disconnect');
      console.log('[Disconnect] WhatsApp instance deletion initiated', data);

      // DON'T close dialog yet - keep it open with loading state
      // Dialog will close after polling confirms deletion

      // Start polling to detect when instance is deleted
      if (!pollingActiveRef.current) {
        pollingActiveRef.current = true;
        console.debug('[Disconnect] Starting polling to detect instance deletion');
        
        const loop = (async () => {
          while (pollingActiveRef.current) {
            try {
              console.debug('[Disconnect] Checking if instance is deleted...');
              const { data: checkData } = await api.get('/api/v1/instance_connect');
              
              console.debug('[Disconnect] instance_connect response:', checkData);
              
              // Check if instance doesn't exist (has been deleted)
              if (checkData?.instance_exists === false || checkData?.state === 'not_found') {
                console.log('[Disconnect] Instance confirmed deleted');
                
                // Update UI
                setConnectionState('disconnected');
                setQrCode(null);
                
                // Stop polling
                pollingActiveRef.current = false;
                pollingTaskRef.current = null;
                
                // NOW close the dialog
                setShowDisconnectDialog(false);
                setIsDisconnecting(false);
                
                break;
              }
              
              console.debug('[Disconnect] Instance still exists, waiting 3s before next check');
              await new Promise((res) => setTimeout(res, 3000));
            } catch (e) {
              console.error('[Disconnect] Error in check:', e);
              // Continue polling even on error
              await new Promise((res) => setTimeout(res, 3000));
            }
          }
          console.debug('[Disconnect] Background loop ended');
        })();
        
        pollingTaskRef.current = loop;
      }
      
    } catch (err: any) {
      console.error('[Disconnect] Error:', err);
      
      // Extract user-friendly error message
      let userMessage = 'Unable to disconnect WhatsApp. ';
      
      if (err?.response?.data?.detail) {
        userMessage = err.response.data.detail;
      } else if (err?.code === 'ERR_NETWORK' || err?.message?.includes('Network Error')) {
        userMessage = 'Network connection failed. Please check your internet and try again.';
      } else {
        userMessage = 'An error occurred while disconnecting. Please try again.';
      }
      
      setError(userMessage);
      setIsDisconnecting(false);
      setShowDisconnectDialog(false);
    }
  };

  useEffect(() => {
    // Check initial connection status on mount by calling /instance_connect
    checkInitialConnectionStatus();

    return () => {
      // Stop any in-progress polling loop on unmount
      pollingActiveRef.current = false;
      pollingTaskRef.current = null;
    };
  }, []);

  return (
    <div className="flex h-screen w-full">
      <ChatSidebar currentPath="/chat/sales" />

      <main className="flex-1 overflow-y-auto bg-gradient-to-b from-background to-secondary/20 p-8 pt-16 md:pt-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Sales Connector</h1>
            <p className="text-muted-foreground">
              Connect your WhatsApp Business to automate sales conversations
            </p>
          </div>

          <Card className="glass p-8 border-white/30">
            <div className="flex flex-col items-center text-center space-y-6">
              <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center">
                <MessageCircle className="w-10 h-10 text-primary" />
              </div>

              <div className="space-y-2">
                <h2 className="text-2xl font-bold">WhatsApp Business Integration</h2>
                <p className="text-muted-foreground max-w-md">
                  Connect your WhatsApp Business account to enable AI-powered sales automation,
                  customer support, and order management.
                </p>
              </div>

              {connectionState === 'connected' ? (
                <div className="flex items-center gap-2 text-green-500">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">Connected</span>
                </div>
              ) : connectionState === 'connecting' ? (
                <div className="flex flex-col items-center gap-4">
                  {qrCode ? (
                    <>
                      <img
                        src={`data:image/png;base64,${qrCode}`}
                        alt="WhatsApp QR Code"
                        className="w-48 h-48"
                      />
                      <p className="text-sm text-muted-foreground">
                        Scan this QR code with WhatsApp on your phone to connect
                      </p>
                    </>
                  ) : (
                    <div className="flex items-center gap-2 text-primary">
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span className="font-medium">Generating QR Code...</span>
                    </div>
                  )}
                </div>
              ) : isCheckingStatus ? (
                <div className="flex items-center gap-2 text-primary">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="font-medium">Checking connection status...</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <AlertCircle className="w-5 h-5" />
                  <span className="font-medium">Not Connected</span>
                </div>
              )}

              {error && (
                <div className="text-red-500 text-sm">{error}</div>
              )}

              {connectionState === 'connected' ? (
                <AlertDialog open={showDisconnectDialog} onOpenChange={setShowDisconnectDialog}>
                  <AlertDialogTrigger asChild>
                    <Button
                      size="lg"
                      variant="destructive"
                      className="mt-4"
                      disabled={isDisconnecting}
                    >
                      <MessageCircle className="w-5 h-5 mr-2" />
                      Disconnect WhatsApp Business
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>
                        {isDisconnecting ? 'Disconnecting...' : 'Disconnect WhatsApp Business?'}
                      </AlertDialogTitle>
                      <AlertDialogDescription>
                        {isDisconnecting ? (
                          <div className="flex flex-col items-center gap-3 py-4">
                            <Loader2 className="w-8 h-8 animate-spin text-primary" />
                            <p className="text-center">
                              Disconnecting your WhatsApp Business account...
                              <br />
                              <span className="text-xs text-muted-foreground mt-1">
                                This may take a few seconds
                              </span>
                            </p>
                          </div>
                        ) : (
                          <>
                            Are you sure you want to disconnect your WhatsApp Business account?
                            Once disconnected, your AI agent will no longer be able to reply to customer messages
                            until you reconnect.
                          </>
                        )}
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    {!isDisconnecting && (
                      <AlertDialogFooter>
                        <AlertDialogCancel disabled={isDisconnecting}>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={(e) => {
                            e.preventDefault();
                            disconnectWhatsApp();
                          }}
                          disabled={isDisconnecting}
                          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                          Confirm Disconnect
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    )}
                  </AlertDialogContent>
                </AlertDialog>
              ) : (
                <Button
                  size="lg"
                  className="mt-4"
                  onClick={startConnection}
                  disabled={connectionState !== 'disconnected' || isCheckingStatus}
                  aria-busy={connectionState === 'connecting' || isCheckingStatus}
                >
                  <MessageCircle className="w-5 h-5 mr-2" />
                  {connectionState === 'connecting' ? 'Connecting…' : 'Connect WhatsApp Business'}
                  <ExternalLink className="w-4 h-4 ml-2" />
                </Button>
              )}

              <div className="pt-6 border-t border-border/50 w-full">
                <h3 className="font-semibold mb-4">What you'll get:</h3>
                <ul className="space-y-2 text-left text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                    <span>Automated responses to customer inquiries 24/7</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                    <span>Order tracking and updates sent automatically</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                    <span>Product catalog integration with smart recommendations</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                    <span>Multi-language support for your customers</span>
                  </li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}

export default SalesConnector;
