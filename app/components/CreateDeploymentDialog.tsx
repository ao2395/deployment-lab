'use client'

import { useState } from 'react'
import { Button } from '@/app/components/ui/button'
import { Input } from '@/app/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/app/components/ui/card'
import { Badge } from '@/app/components/ui/badge'
import { Plus, X } from 'lucide-react'
import { DeploymentCreate } from '@/app/lib/api'

interface CreateDeploymentDialogProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (deployment: DeploymentCreate) => void
  isLoading: boolean
}

export function CreateDeploymentDialog({ 
  isOpen, 
  onClose, 
  onSubmit, 
  isLoading 
}: CreateDeploymentDialogProps) {
  const [formData, setFormData] = useState({
    github_url: '',
    subdomain: '',
    env_vars: {} as Record<string, string>
  })
  const [newEnvKey, setNewEnvKey] = useState('')
  const [newEnvValue, setNewEnvValue] = useState('')

  const addEnvVar = () => {
    if (newEnvKey && newEnvValue) {
      console.log('Adding env var:', newEnvKey, '=', newEnvValue)
      console.log('Current env_vars before:', formData.env_vars)
      setFormData(prev => {
        const newFormData = {
          ...prev,
          env_vars: {
            ...prev.env_vars,
            [newEnvKey]: newEnvValue
          }
        }
        console.log('New env_vars after:', newFormData.env_vars)
        return newFormData
      })
      setNewEnvKey('')
      setNewEnvValue('')
    }
  }

  const removeEnvVar = (key: string) => {
    setFormData(prev => {
      const newEnvVars = { ...prev.env_vars }
      delete newEnvVars[key]
      return {
        ...prev,
        env_vars: newEnvVars
      }
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Form submit - formData:', formData)
    console.log('Form submit - env_vars:', formData.env_vars)
    onSubmit(formData)
  }

  const resetForm = () => {
    setFormData({
      github_url: '',
      subdomain: '',
      env_vars: {}
    })
    setNewEnvKey('')
    setNewEnvValue('')
  }

  const handleClose = () => {
    resetForm()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Create New Deployment</CardTitle>
            <Button variant="ghost" size="sm" onClick={handleClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="github_url" className="text-sm font-medium">
                GitHub Repository URL *
              </label>
              <Input
                id="github_url"
                type="url"
                placeholder="https://github.com/username/repository"
                value={formData.github_url}
                onChange={(e) => setFormData(prev => ({ ...prev, github_url: e.target.value }))}
                required
              />
              <p className="text-xs text-gray-500">
                The repository must be public or accessible with the configured GitHub token
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="subdomain" className="text-sm font-medium">
                Subdomain *
              </label>
              <Input
                id="subdomain"
                type="text"
                placeholder="my-app"
                value={formData.subdomain}
                onChange={(e) => setFormData(prev => ({ ...prev, subdomain: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '') }))}
                required
              />
              <p className="text-xs text-gray-500">
                Will be accessible at: {formData.subdomain || 'subdomain'}.{process.env.NEXT_PUBLIC_BASE_DOMAIN || 'yourdomain.com'}
              </p>
            </div>

            <div className="space-y-3">
              <label className="text-sm font-medium">Environment Variables</label>
              
              {Object.entries(formData.env_vars).length > 0 && (
                <div className="space-y-2">
                  {Object.entries(formData.env_vars).map(([key, value]) => (
                    <div key={key} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                      <Badge variant="outline">{key}</Badge>
                      <span className="text-sm text-gray-600 flex-1">{value}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeEnvVar(key)}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <Input
                  placeholder="Key (e.g., DATABASE_URL)"
                  value={newEnvKey}
                  onChange={(e) => setNewEnvKey(e.target.value)}
                />
                <Input
                  placeholder="Value"
                  value={newEnvValue}
                  onChange={(e) => setNewEnvValue(e.target.value)}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    console.log('Add button clicked!')
                    console.log('newEnvKey:', newEnvKey)
                    console.log('newEnvValue:', newEnvValue)
                    console.log('Button disabled?', !newEnvKey || !newEnvValue)
                    addEnvVar()
                  }}
                  disabled={!newEnvKey || !newEnvValue}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isLoading}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isLoading || !formData.github_url || !formData.subdomain}
                className="flex-1"
              >
                {isLoading ? 'Creating...' : 'Create Deployment'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}