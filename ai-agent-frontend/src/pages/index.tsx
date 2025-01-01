import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.push('/login'); // Redirect to the login page
  }, [router]);

  return null; // No need to display anything as we're redirecting
}