export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-sm w-full text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Lighthouse</h1>
        <p className="text-gray-500 mb-6">Data Transformation Platform</p>
        <a
          href="/api/v1/auth/login"
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors w-full justify-center"
        >
          Sign in with Google
        </a>
      </div>
    </div>
  );
}
