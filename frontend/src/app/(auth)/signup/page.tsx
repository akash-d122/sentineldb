import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { createClient } from "@/utils/supabase/server";
import { redirect } from "next/navigation";

export default async function SignupPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const resolvedParams = await searchParams;
  const errorMsg = resolvedParams.error;
  const signUp = async (formData: FormData) => {
    "use server";
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const supabase = await createClient();

    const { error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      return redirect("/signup?error=Could not create user");
    }

    return redirect("/");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">SentinelDB Sign Up</CardTitle>
          <CardDescription>Enter your email below to create a new account</CardDescription>
        </CardHeader>
        <CardContent>
          {errorMsg && (
            <div className="bg-red-50 text-red-500 p-3 mb-4 rounded text-sm">
              {errorMsg}
            </div>
          )}
          <form className="space-y-4" action={signUp}>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" name="email" type="email" placeholder="m@example.com" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" name="password" type="password" required />
            </div>
                        <Button type="submit" className="w-full">Sign Up</Button>
            <div className="text-center text-sm mt-4">
              <a href="/login" className="text-blue-600 hover:underline">Already have an account? Login here</a>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
