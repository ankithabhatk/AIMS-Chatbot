import { authenticateUser, issueAuthToken } from '../../../../../services/authStore.server';

export const runtime = 'nodejs';

type LoginPayload = {
  email?: string;
  password?: string;
};

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as LoginPayload;

    if (!body.email || !body.password) {
      return Response.json(
        { success: false, message: 'Email and password are required' },
        { status: 400 }
      );
    }

    const user = await authenticateUser(body.email, body.password);

    if (!user) {
      return Response.json(
        { success: false, message: 'Invalid email or password' },
        { status: 401 }
      );
    }

    return Response.json(
      {
        success: true,
        message: 'Login successful',
        user,
        token: issueAuthToken(user),
      },
      { status: 200 }
    );
  } catch {
    return Response.json(
      { success: false, message: 'Login failed' },
      { status: 500 }
    );
  }
}
