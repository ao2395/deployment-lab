'use client'

import { Deployment } from '@/app/lib/api'
import { Card, CardContent, CardHeader } from '@/app/components/ui/card'
import { Button } from '@/app/components/ui/button'
import { Badge } from '@/app/components/ui/badge'
import { ExternalLink, Eye, Trash2 } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface DeploymentCardProps {
  deployment: Deployment
  onDelete: (deployment: Deployment) => void
}

function getStatusVariant(status: string) {
  switch (status) {
    case 'running':
      return 'success'
    case 'building':
      return 'info' 
    case 'pending':
      return 'warning'
    case 'failed':
      return 'destructive'
    case 'stopped':
      return 'secondary'
    default:
      return 'default'
  }
}

export function DeploymentCard({ deployment, onDelete }: DeploymentCardProps) {
  const router = useRouter()
  const baseDomain = process.env.NEXT_PUBLIC_BASE_DOMAIN || 'yourdomain.com'

  const handleDelete = () => {
    if (confirm(`Delete deployment "${deployment.name}"? This action cannot be undone.`)) {
      onDelete(deployment)
    }
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <h3 className="font-semibold text-lg">{deployment.name}</h3>
            <p className="text-sm text-gray-600">
              {deployment.subdomain}.{baseDomain}
            </p>
            <p className="text-xs text-gray-500">
              Port: {deployment.port}
            </p>
          </div>
          <Badge variant={getStatusVariant(deployment.status)}>
            {deployment.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="text-sm">
            <span className="text-gray-500">GitHub: </span>
            <a 
              href={deployment.github_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              {deployment.github_url.split('/').slice(-2).join('/')}
            </a>
          </div>
          
          <div className="text-xs text-gray-500">
            Created: {new Date(deployment.created_at).toLocaleDateString()}
          </div>

          <div className="flex gap-2 pt-2">
            {deployment.status === 'running' && (
              <Button 
                variant="outline" 
                size="sm" 
                asChild
                className="flex items-center gap-1"
              >
                <a 
                  href={`https://${deployment.subdomain}.${baseDomain}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-3 w-3" />
                  Visit
                </a>
              </Button>
            )}
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => router.push(`/deployments/${deployment.id}/logs`)}
              className="flex items-center gap-1"
            >
              <Eye className="h-3 w-3" />
              Logs
            </Button>
            
            <Button 
              variant="destructive" 
              size="sm"
              onClick={handleDelete}
              className="flex items-center gap-1"
            >
              <Trash2 className="h-3 w-3" />
              Delete
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}