export default function OnboardingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">Welcome to SentinelDB</h1>
          <p className="text-gray-500 mt-2">Let's get your workspace set up.</p>
        </div>
        {children}
      </div>
    </div>
  );
}
