import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, ChartBar } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const Login = ({ onLogin }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isRegisterMode, setIsRegisterMode] = useState(false)

  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  })

  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    organization_name: ''
  })

  const handleLogin = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const response = await fetch(apiUrl('/api/auth/login'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginForm),
      })

      const data = await response.json()

      if (response.ok) {
        localStorage.setItem('token', data.token)
        onLogin(data.user, data.organization, data.permissions || [], data.accessible_departments || [])
      } else {
        setError(data.message || 'Login failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    if (registerForm.password !== registerForm.confirmPassword) {
      setError('Passwords do not match')
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch(apiUrl('/api/auth/register'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password,
          first_name: registerForm.first_name,
          last_name: registerForm.last_name,
          organization_name: registerForm.organization_name
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setIsRegisterMode(false)
        setError('')
        // Clear form
        setRegisterForm({
          username: '',
          email: '',
          password: '',
          confirmPassword: '',
          first_name: '',
          last_name: '',
          organization_name: ''
        })
        // Show success message
        setError('Registration successful! Please log in.')
      } else {
        setError(data.message || 'Registration failed')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }


  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 to-blue-800 p-12 flex-col justify-center relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute transform rotate-45 -left-1/4 -top-1/4 w-96 h-96 bg-white rounded-full"></div>
          <div className="absolute transform rotate-45 -right-1/4 -bottom-1/4 w-96 h-96 bg-white rounded-full"></div>
        </div>
        
        {/* Content */}
        <div className="relative z-10 text-center">
          <div className="flex items-center justify-center space-x-4 mb-12">
            <div className="bg-white/20 backdrop-blur-sm p-4 rounded-lg">
              <ChartBar className="h-12 w-12 text-white" />
            </div>
            <div className="text-left">
              <h1 className="text-5xl font-bold text-white">BIS</h1>
              <p className="text-blue-100 text-lg">Business Intelligence for Softbase</p>
            </div>
          </div>

          <div className="space-y-6">
            <h2 className="text-4xl font-bold text-white">
              Real Time Dashboards
            </h2>
            <p className="text-xl text-blue-100 max-w-md mx-auto">
              Comprehensive reporting and analytics for Softbase Evolution
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden mb-8 text-center">
            <div className="inline-flex items-center space-x-3">
              <div className="bg-blue-600 p-3 rounded-lg">
                <ChartBar className="h-8 w-8 text-white" />
              </div>
              <div className="text-left">
                <h1 className="text-2xl font-bold text-gray-900">BIS</h1>
                <p className="text-gray-600 text-sm">Business Intelligence for Softbase</p>
              </div>
            </div>
          </div>

          <div className="bg-white shadow-xl rounded-2xl p-8">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900">
                {isRegisterMode ? 'Create Account' : 'Welcome Back'}
              </h2>
              <p className="text-gray-600 mt-2">
                {isRegisterMode 
                  ? 'Register your organization to get started' 
                  : 'Sign in to access your dashboard'}
              </p>
            </div>

            {!isRegisterMode ? (
              <form onSubmit={handleLogin} className="space-y-6">
                <div>
                  <Label htmlFor="username" className="text-sm font-medium text-gray-700">
                    Username
                  </Label>
                  <Input
                    id="username"
                    type="text"
                    className="mt-1"
                    placeholder="Enter your username"
                    value={loginForm.username}
                    onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                    required
                  />
                </div>
                
                <div>
                  <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                    Password
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    className="mt-1"
                    placeholder="Enter your password"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    required
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <input
                      id="remember-me"
                      name="remember-me"
                      type="checkbox"
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                      Remember me
                    </label>
                  </div>
                  <button type="button" className="text-sm text-blue-600 hover:text-blue-500">
                    Forgot password?
                  </button>
                </div>

                {error && !error.includes('successful') && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {error && error.includes('successful') && (
                  <Alert className="bg-green-50 border-green-200">
                    <AlertDescription className="text-green-800">{error}</AlertDescription>
                  </Alert>
                )}

                <Button 
                  type="submit" 
                  className="w-full bg-blue-600 hover:bg-blue-700" 
                  disabled={isLoading}
                >
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Sign In
                </Button>

                <div className="text-center">
                  <span className="text-sm text-gray-600">
                    Don't have an account?{' '}
                    <button
                      type="button"
                      onClick={() => setIsRegisterMode(true)}
                      className="font-medium text-blue-600 hover:text-blue-500"
                    >
                      Sign up
                    </button>
                  </span>
                </div>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="first_name" className="text-sm font-medium text-gray-700">
                      First Name
                    </Label>
                    <Input
                      id="first_name"
                      type="text"
                      className="mt-1"
                      value={registerForm.first_name}
                      onChange={(e) => setRegisterForm({ ...registerForm, first_name: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="last_name" className="text-sm font-medium text-gray-700">
                      Last Name
                    </Label>
                    <Input
                      id="last_name"
                      type="text"
                      className="mt-1"
                      value={registerForm.last_name}
                      onChange={(e) => setRegisterForm({ ...registerForm, last_name: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="reg_username" className="text-sm font-medium text-gray-700">
                    Username
                  </Label>
                  <Input
                    id="reg_username"
                    type="text"
                    className="mt-1"
                    value={registerForm.username}
                    onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    className="mt-1"
                    value={registerForm.email}
                    onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="organization_name" className="text-sm font-medium text-gray-700">
                    Organization Name
                  </Label>
                  <Input
                    id="organization_name"
                    type="text"
                    className="mt-1"
                    value={registerForm.organization_name}
                    onChange={(e) => setRegisterForm({ ...registerForm, organization_name: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="reg_password" className="text-sm font-medium text-gray-700">
                    Password
                  </Label>
                  <Input
                    id="reg_password"
                    type="password"
                    className="mt-1"
                    value={registerForm.password}
                    onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="confirm_password" className="text-sm font-medium text-gray-700">
                    Confirm Password
                  </Label>
                  <Input
                    id="confirm_password"
                    type="password"
                    className="mt-1"
                    value={registerForm.confirmPassword}
                    onChange={(e) => setRegisterForm({ ...registerForm, confirmPassword: e.target.value })}
                    required
                  />
                </div>

                {error && !error.includes('successful') && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <Button 
                  type="submit" 
                  className="w-full bg-blue-600 hover:bg-blue-700" 
                  disabled={isLoading}
                >
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create Account
                </Button>

                <div className="text-center">
                  <span className="text-sm text-gray-600">
                    Already have an account?{' '}
                    <button
                      type="button"
                      onClick={() => setIsRegisterMode(false)}
                      className="font-medium text-blue-600 hover:text-blue-500"
                    >
                      Sign in
                    </button>
                  </span>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login