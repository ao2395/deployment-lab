'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ProtectedRoute } from '@/app/components/ProtectedRoute'
import { DeploymentCard } from '@/app/components/DeploymentCard'
import { CreateDeploymentDialog } from '@/app/components/CreateDeploymentDialog'
import { Button } from '@/app/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card'
import { useAuth } from '@/app/hooks/useAuth'
import { useToast } from '@/app/hooks/use-toast'
import { deploymentsAPI, Deployment, DeploymentCreate } from '@/app/lib/api'
import { Plus, LogOut, RefreshCw } from 'lucide-react'

export default function DashboardPage() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const { user, logout } = useAuth()
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { 
    data: deployments = [], 
    isLoading, 
    refetch 
  } = useQuery({
    queryKey: ['deployments'],
    queryFn: async () => {
      const response = await deploymentsAPI.list()
      return response.data
    },
    refetchInterval: 5000, // Refetch every 5 seconds for real-time updates
  })

  const createDeploymentMutation = useMutation({
    mutationFn: async (deployment: DeploymentCreate) => {
      const response = await deploymentsAPI.create(deployment)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
      setIsCreateDialogOpen(false)
      toast({
        title: "Deployment created",
        description: "Your deployment is being built. Check the logs for progress.",
      })
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error ? error.message : 
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 
        "Failed to create deployment"
      toast({
        title: "Deployment failed",
        description: errorMessage,
        variant: "destructive",
      })
    }
  })

  const deleteDeploymentMutation = useMutation({
    mutationFn: async (deploymentId: string) => {
      await deploymentsAPI.delete(deploymentId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
      toast({
        title: "Deployment deleted",
        description: "The deployment and all its resources have been removed.",
      })
    },
    onError: (error: unknown) => {
      const errorMessage = error instanceof Error ? error.message : 
        (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 
        "Failed to delete deployment"
      toast({
        title: "Delete failed",
        description: errorMessage,
        variant: "destructive",
      })
    }
  })

  const handleCreateDeployment = (deployment: DeploymentCreate) => {
    createDeploymentMutation.mutate(deployment)
  }

  const handleDeleteDeployment = (deployment: Deployment) => {
    deleteDeploymentMutation.mutate(deployment.id)
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-black">
        {/* Header */}
        <header className="bg-gray-900 shadow-sm border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Auto Deploy Manager
                </h1>
                <p className="text-sm text-gray-300">
                  Welcome back, {user?.username}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetch()}
                  disabled={isLoading}
                >
                  <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={logout}
                >
                  <LogOut className="h-4 w-4 mr-1" />
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Total Deployments
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{deployments.length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Running
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {deployments.filter(d => d.status === 'running').length}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Building
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">
                  {deployments.filter(d => d.status === 'building').length}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">
                  Failed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-600">
                  {deployments.filter(d => d.status === 'failed').length}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Deployments Section */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-white">Deployments</h2>
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Deployment
            </Button>
          </div>

          {/* Deployments Grid */}
          {isLoading && deployments.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            </div>
          ) : deployments.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <div className="text-gray-300 text-center">
                  <h3 className="text-lg font-medium mb-2 text-white">No deployments yet</h3>
                  <p className="text-sm mb-4">
                    Create your first deployment to get started
                  </p>
                  <Button onClick={() => setIsCreateDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Deployment
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {deployments.map((deployment) => (
                <DeploymentCard
                  key={deployment.id}
                  deployment={deployment}
                  onDelete={handleDeleteDeployment}
                />
              ))}
            </div>
          )}
        </main>

        {/* Create Deployment Dialog */}
        <CreateDeploymentDialog
          isOpen={isCreateDialogOpen}
          onClose={() => setIsCreateDialogOpen(false)}
          onSubmit={handleCreateDeployment}
          isLoading={createDeploymentMutation.isPending}
        />
      </div>
    </ProtectedRoute>
  )
}