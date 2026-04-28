import { createUser, issueAuthToken } from '../../../../../services/authStore.server';
import type { SignupData } from '../../../../../types/auth';

export const runtime = 'nodejs';

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as Partial<SignupData>;

    if (!body.email || !body.password || !body.name || !body.role) {
      return Response.json(
        { success: false, message: 'Missing required fields' },
        { status: 400 }
      );
    }

    const user = await createUser({
      email: body.email,
      password: body.password,
      name: body.name,
      role: body.role,
      organization_type: body.organization_type,
      organization_name: body.organization_name,
      organization_code: body.organization_code,
      department: body.department,
      title: body.title,
    });

    return Response.json(
      {
        success: true,
        message: 'Account created successfully',
        user,
        token: issueAuthToken(user),
      },
      { status: 201 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Signup failed';
    const status = message === 'User already exists' ? 409 : 500;

    return Response.json(
      { success: false, message },
      { status }
    );
  }
}
