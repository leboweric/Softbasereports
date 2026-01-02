import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Eye, EyeOff } from 'lucide-react'
import { apiUrl } from '@/lib/api'

const Login = ({ onLogin }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isRegisterMode, setIsRegisterMode] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

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
        
        const userWithNavigation = {
          ...data.user,
          navigation: data.navigation || {},
          resources: data.resources || [],
          permissions_summary: data.permissions_summary || {}
        }
        onLogin(userWithNavigation, data.organization, data.permissions || [], data.accessible_departments || [])
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
        setRegisterForm({
          username: '',
          email: '',
          password: '',
          confirmPassword: '',
          first_name: '',
          last_name: '',
          organization_name: ''
        })
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
      {/* Left Panel - Login Form */}
      <div className="w-full lg:w-[45%] flex flex-col justify-center px-8 lg:px-16 py-12 bg-white">
        <div className="w-full max-w-md mx-auto">
          {/* Logo */}
          <div className="mb-12">
            <img 
              src="/aiop_logo.png" 
              alt="AIOP" 
              className="h-12 w-auto"
            />
          </div>

          {/* Form Header */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900">
              {isRegisterMode ? 'Create Account' : 'Log In'}
            </h2>
          </div>

          {!isRegisterMode ? (
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <Label htmlFor="username" className="text-sm font-medium text-gray-700">
                  Email*
                </Label>
                <Input
                  id="username"
                  type="text"
                  className="mt-2 h-12"
                  placeholder="name@company.com"
                  value={loginForm.username}
                  onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="password" className="text-sm font-medium text-gray-700">
                  Password*
                </Label>
                <div className="relative mt-2">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    className="h-12 pr-12"
                    placeholder="••••••••••••"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    required
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
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
                    Remember Me
                  </label>
                </div>
                <button type="button" className="text-sm font-medium text-gray-900 hover:text-gray-700 uppercase tracking-wide">
                  Forgot Password?
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
                className="w-full h-12 bg-[#0f172a] hover:bg-[#1e293b] text-white font-medium rounded-lg" 
                disabled={isLoading}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                LOG IN
              </Button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white text-gray-500">OR</span>
                </div>
              </div>

              <Button 
                type="button"
                variant="outline"
                className="w-full h-12 border-gray-300 hover:bg-gray-50 font-medium"
                disabled
              >
                <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Log in with Google
              </Button>

              <Button 
                type="button"
                variant="outline"
                className="w-full h-12 border-gray-300 hover:bg-gray-50 font-medium"
                disabled
              >
                <svg className="mr-2 h-5 w-5" viewBox="0 0 23 23">
                  <path fill="#f35325" d="M1 1h10v10H1z"/>
                  <path fill="#81bc06" d="M12 1h10v10H12z"/>
                  <path fill="#05a6f0" d="M1 12h10v10H1z"/>
                  <path fill="#ffba08" d="M12 12h10v10H12z"/>
                </svg>
                Log in with Microsoft
              </Button>

              <div className="text-center pt-4">
                <span className="text-sm text-gray-600">
                  Don't have an account yet?{' '}
                  <button
                    type="button"
                    onClick={() => setIsRegisterMode(true)}
                    className="font-semibold text-gray-900 hover:text-gray-700 uppercase tracking-wide"
                  >
                    Sign Up
                  </button>
                </span>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="first_name" className="text-sm font-medium text-gray-700">
                    First Name*
                  </Label>
                  <Input
                    id="first_name"
                    type="text"
                    className="mt-2 h-12"
                    value={registerForm.first_name}
                    onChange={(e) => setRegisterForm({ ...registerForm, first_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="last_name" className="text-sm font-medium text-gray-700">
                    Last Name*
                  </Label>
                  <Input
                    id="last_name"
                    type="text"
                    className="mt-2 h-12"
                    value={registerForm.last_name}
                    onChange={(e) => setRegisterForm({ ...registerForm, last_name: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="reg_username" className="text-sm font-medium text-gray-700">
                  Username*
                </Label>
                <Input
                  id="reg_username"
                  type="text"
                  className="mt-2 h-12"
                  value={registerForm.username}
                  onChange={(e) => setRegisterForm({ ...registerForm, username: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="reg_email" className="text-sm font-medium text-gray-700">
                  Email*
                </Label>
                <Input
                  id="reg_email"
                  type="email"
                  className="mt-2 h-12"
                  placeholder="name@company.com"
                  value={registerForm.email}
                  onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="organization_name" className="text-sm font-medium text-gray-700">
                  Organization Name*
                </Label>
                <Input
                  id="organization_name"
                  type="text"
                  className="mt-2 h-12"
                  value={registerForm.organization_name}
                  onChange={(e) => setRegisterForm({ ...registerForm, organization_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="reg_password" className="text-sm font-medium text-gray-700">
                  Password*
                </Label>
                <Input
                  id="reg_password"
                  type="password"
                  className="mt-2 h-12"
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                  required
                />
              </div>

              <div>
                <Label htmlFor="confirm_password" className="text-sm font-medium text-gray-700">
                  Confirm Password*
                </Label>
                <Input
                  id="confirm_password"
                  type="password"
                  className="mt-2 h-12"
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

              {error && error.includes('successful') && (
                <Alert className="bg-green-50 border-green-200">
                  <AlertDescription className="text-green-800">{error}</AlertDescription>
                </Alert>
              )}

              <Button 
                type="submit" 
                className="w-full h-12 bg-[#0f172a] hover:bg-[#1e293b] text-white font-medium rounded-lg" 
                disabled={isLoading}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                CREATE ACCOUNT
              </Button>

              <div className="text-center pt-4">
                <span className="text-sm text-gray-600">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => setIsRegisterMode(false)}
                    className="font-semibold text-gray-900 hover:text-gray-700 uppercase tracking-wide"
                  >
                    Log In
                  </button>
                </span>
              </div>
            </form>
          )}

          {/* Footer */}
          <div className="mt-8 text-center text-xs text-gray-500">
            By continuing, you agree to the{' '}
            <a href="#" className="underline hover:text-gray-700">Terms and Conditions</a>
            {' '}and{' '}
            <a href="#" className="underline hover:text-gray-700">Privacy Policy</a>.
          </div>
        </div>
      </div>

      {/* Right Panel - Image */}
      <div 
        className="hidden lg:block lg:w-[55%] bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: 'url(/login_bg.jpg)' }}
      >
        {/* Optional overlay for better contrast if needed */}
        {/* <div className="w-full h-full bg-black/10"></div> */}
      </div>
    </div>
  )
}

export default Login
