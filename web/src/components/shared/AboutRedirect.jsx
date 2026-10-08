import React from 'react';

export default function AboutRedirect({user}) {
  React.useEffect(() => {
    if (process.env.NODE_ENV != 'development' && user === null) {
      if (window.location.hostname.endsWith('.nip.io')) {
        window.location = '/api/public/auth/login';
        return;
      }
      window.location = 'https://about.anubis-lms.io/';
      window.reload(false);
    }
  }, [user]);
  return null;
}
