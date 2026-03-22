import { Compass } from 'lucide-react';

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f]">
      <div className="bg-[#0d0d14] border border-[#1a1a25] rounded-xl p-8 max-w-sm w-full text-center shadow-2xl">
        <div className="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center mx-auto mb-4">
          <Compass size={22} className="text-white" />
        </div>
        <h1 className="text-xl font-semibold text-white mb-1">Lighthouse</h1>
        <p className="text-[13px] text-[#5a5a6b] mb-8">Data Transformation Platform</p>
        <a
          href="/api/v1/auth/login"
          className="inline-flex items-center justify-center gap-2 bg-white text-[#0a0a0f] px-6 py-3 rounded-lg text-[14px] font-medium hover:bg-gray-100 transition-colors w-full"
        >
          Sign in with Google
        </a>
      </div>
    </div>
  );
}
