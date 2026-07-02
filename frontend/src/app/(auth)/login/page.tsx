import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { createClient } from "@/utils/supabase/server";
import { redirect } from "next/navigation";

export default function LoginPage() {
  const signIn = async (formData: FormData) => {
    "use server";
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;
    const supabase = await createClient();

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      return redirect("/login?error=Could not authenticate user");
    }

    return redirect("/");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">SentinelDB Login</CardTitle>
          <CardDescription>Enter your email below to login to your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" action={signIn}>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" name="email" type="email" placeholder="m@example.com" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" name="password" type="password" required />
            </div>
                        <Button type="submit" className="w-full">Login</Button>
            <div className="text-center text-sm mt-4">
              <a href="/signup" className="text-blue-600 hover:underline">Need an account? Sign up here</a>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
