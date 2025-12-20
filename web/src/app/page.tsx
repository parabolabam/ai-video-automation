import { redirect } from 'next/navigation';

export default function Home() {
  // For MVP, auto-redirect to the seed user
  redirect('/user/cb176b48-0995-41e2-8dda-2b80b29cb94d');
}
