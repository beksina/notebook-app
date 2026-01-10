import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile, trigger }) {
      if (account && profile) {
        token.googleId = profile.sub;
        token.email = profile.email;
        token.name = profile.name;
        token.picture = profile.picture;

        // Sync user with backend on sign-in
        try {
          const response = await fetch(`${API_URL}/api/auth/sync`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              google_id: profile.sub,
              email: profile.email,
              name: profile.name,
              image: profile.picture,
            }),
          });
          
          if (response.ok) {
            const data = await response.json();
            token.userId = data.id;
            token.accessToken = data.access_token;  // Store JWT token
          }
        } catch (error) {
          console.error("Failed to sync user with backend:", error);
        }
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.userId as string;
        session.user.googleId = token.googleId as string;
      }
      // Expose JWT token to client-side session
      (session as any).accessToken = token.accessToken;
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
});
