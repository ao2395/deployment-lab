'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { ProtectedRoute } from '@/app/components/ProtectedRoute'
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card'
import { Button } from '@/app/components/ui/button'
import { Badge } from '@/app/components/ui/badge'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import { deploymentsAPI } from '@/app/lib/api'
import { useEffect, useRef } from 'react'

function getLogLevelColor(level: string) {
  switch (level.toLowerCase()) {
    case 'error':
      return 'text-red-600'
    case 'warning':
      return 'text-yellow-600'
    case 'info':
      return 'text-blue-600'
    case 'debug':
      return 'text-gray-600'
    default:
      return 'text-gray-700'
  }
}

function getLogLevelBadge(level: string) {
  switch (level.toLowerCase()) {
    case 'error':
      return 'destructive'
    case 'warning':
      return 'warning'
    case 'info':
      return 'info'
    case 'debug':
      return 'secondary'
    default:
      return 'default'
  }
}

export default function DeploymentLogsPage() {
  const params = useParams()
  const router = useRouter()
  const deploymentId = params.id as string
  const logsEndRef = useRef<HTMLDivElement>(null)

  const { data: deployment, isLoading: deploymentLoading } = useQuery({
    queryKey: ['deployment', deploymentId],
    queryFn: async () => {
      const response = await deploymentsAPI.get(deploymentId)
      return response.data
    },
  })

  const { 
    data: logs = [], 
    isLoading: logsLoading, 
    refetch: refetchLogs 
  } = useQuery({
    queryKey: ['logs', deploymentId],
    queryFn: async () => {
      const response = await deploymentsAPI.getLogs(deploymentId)
      return response.data
    },
    refetchInterval: 2000, // Refetch every 2 seconds for real-time logs
  })

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  if (deploymentLoading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      </ProtectedRoute>
    )
  }

  if (!deployment) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">Deployment not found</h2>
            <Button onClick={() => router.push('/dashboard')}>
              Return to Dashboard
            </Button>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-black">
        {/* Header */}
        <header className="bg-gray-900 shadow-sm border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between py-4">
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push('/dashboard')}
                  className="text-white hover:text-gray-300"
                >
                  <ArrowLeft className="h-4 w-4 mr-1" />
                  Back
                </Button>
                <div>
                  <h1 className="text-xl font-bold text-white">
                    {deployment.name} - Build Logs
                  </h1>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={deployment.status === 'running' ? 'success' : 
                                  deployment.status === 'building' ? 'info' :
                                  deployment.status === 'failed' ? 'destructive' : 'secondary'}>
                      {deployment.status}
                    </Badge>
                    <span className="text-sm text-gray-300">
                      {deployment.subdomain}.{process.env.NEXT_PUBLIC_BASE_DOMAIN || 'yourdomain.com'}
                    </span>
                  </div>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchLogs()}
                disabled={logsLoading}
              >
                <RefreshCw className={`h-4 w-4 ${logsLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </header>

        {/* Logs Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Build & Deployment Logs</span>
                <span className="text-sm font-normal text-gray-300">
                  {logs.length} entries
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-black rounded-lg p-4 max-h-[600px] overflow-y-auto font-mono text-sm">
                {logs.length === 0 ? (
                  <div className="text-gray-400 text-center py-8">
                    No logs available yet...
                  </div>
                ) : (
                  <div className="space-y-1">
                    {logs.map((log) => (
                      <div key={log.id} className="flex items-start gap-3">
                        <span className="text-gray-500 text-xs min-w-[80px]">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <Badge 
                          variant={getLogLevelBadge(log.log_level) as "default" | "destructive" | "secondary" | "outline"}
                          className="text-xs min-w-[60px] justify-center"
                        >
                          {log.log_level.toUpperCase()}
                        </Badge>
                        <span className={`${getLogLevelColor(log.log_level)} flex-1`}>
                          {log.message}
                        </span>
                      </div>
                    ))}
                    <div ref={logsEndRef} />
                  </div>
                )}
              </div>
              
              {logs.length > 0 && (
                <div className="mt-4 text-xs text-gray-400 text-center">
                  Logs update automatically every 2 seconds
                </div>
              )}
            </CardContent>
          </Card>
        </main>
      </div>
    </ProtectedRoute>
  )
}