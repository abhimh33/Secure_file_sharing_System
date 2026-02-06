import { useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { Shield, Mail, Loader2, ArrowLeft, CheckCircle } from 'lucide-react';
import { authApi } from '../../api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');

  const validateEmail = () => {
    if (!email) {
      setError('Email is required');
      return false;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('Invalid email format');
      return false;
    }
    setError('');
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateEmail()) return;
    
    setIsLoading(true);
    
    try {
      await authApi.forgotPassword(email);
      setIsSubmitted(true);
      toast.success('Password reset instructions sent!');
    } catch {
      // Even if email doesn't exist, show success for security
      setIsSubmitted(true);
      toast.success('If this email exists, reset instructions have been sent.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl shadow-lg mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Forgot Password</h1>
          <p className="text-gray-600 mt-1">
            {isSubmitted 
              ? 'Check your email for reset instructions'
              : 'Enter your email to reset your password'}
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {isSubmitted ? (
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Check Your Email
              </h2>
              <p className="text-gray-600 text-sm mb-6">
                If an account exists with <strong>{email}</strong>, you will receive 
                password reset instructions shortly.
              </p>
              <p className="text-gray-500 text-xs mb-6">
                Didn't receive an email? Check your spam folder or try again.
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => setIsSubmitted(false)}
                  className="btn btn-secondary w-full"
                >
                  Try Another Email
                </button>
                <Link
                  to="/login"
                  className="btn btn-primary w-full inline-flex items-center justify-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Login
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email */}
              <div>
                <label htmlFor="email" className="label">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`input pl-10 ${error ? 'input-error' : ''}`}
                    placeholder="you@example.com"
                  />
                </div>
                {error && (
                  <p className="mt-1 text-sm text-red-600">{error}</p>
                )}
              </div>

              {/* Info Box */}
              <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
                <p className="text-xs text-blue-700">
                  Enter your registered email address and we'll send you instructions 
                  to reset your password.
                </p>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="btn btn-primary w-full flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Sending...
                  </>
                ) : (
                  'Send Reset Instructions'
                )}
              </button>

              {/* Back to Login */}
              <Link
                to="/login"
                className="btn btn-secondary w-full inline-flex items-center justify-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Login
              </Link>
            </form>
          )}
        </div>

        {/* Help text */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Need help? Contact support at support@securefile.com
          </p>
        </div>
      </div>
    </div>
  );
}
