import os

filepath = "frontend/src/app/t/[tenantId]/incidents/page.tsx"
with open(filepath, "r") as f:
    code = f.read()

# Replace getSession with getUser
code = code.replace("await supabase.auth.getSession()", "await supabase.auth.getUser()")
code = code.replace("const { data: { session } }", "const { data: { user } }")
code = code.replace("if (!session) {", "if (!user) {")
code = code.replace("Authorization: `Bearer ${session.access_token}`", "Authorization: `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`")

with open(filepath, "w") as f:
    f.write(code)
