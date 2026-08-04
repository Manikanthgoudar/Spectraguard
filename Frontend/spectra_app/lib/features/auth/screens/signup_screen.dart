import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:spectra_app/core/auth/auth_provider.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';

const _roles = ['public', 'pharmacist', 'investigator'];

class SignupScreen extends ConsumerStatefulWidget {
  const SignupScreen({super.key});

  @override
  ConsumerState<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends ConsumerState<SignupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _orgCtrl = TextEditingController();
  final _licenseCtrl = TextEditingController();
  final _designationCtrl = TextEditingController();
  final _cityCtrl = TextEditingController();
  String _role = 'public';
  bool _obscure = true;

  bool get _needsLicense => _role == 'pharmacist' || _role == 'investigator';

  @override
  void dispose() {
    for (final c in [
      _nameCtrl, _emailCtrl, _passwordCtrl, _phoneCtrl,
      _orgCtrl, _licenseCtrl, _designationCtrl, _cityCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    await ref.read(authProvider.notifier).signup(
          fullName: _nameCtrl.text.trim(),
          email: _emailCtrl.text.trim(),
          password: _passwordCtrl.text,
          phone: _phoneCtrl.text.trim().isEmpty
              ? null
              : _phoneCtrl.text.trim(),
          role: _role,
          organization: _orgCtrl.text.trim().isEmpty
              ? null
              : _orgCtrl.text.trim(),
          licenseNumber: _licenseCtrl.text.trim().isEmpty
              ? null
              : _licenseCtrl.text.trim(),
          designation: _designationCtrl.text.trim().isEmpty
              ? null
              : _designationCtrl.text.trim(),
          city: _cityCtrl.text.trim().isEmpty
              ? null
              : _cityCtrl.text.trim(),
        );
    final error = ref.read(authProvider).error;
    if (error != null && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error), backgroundColor: AppColors.error),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: context.isWide ? _wideBody(context) : _mobileBody(context),
    );
  }

  // ── Mobile body (original layout preserved) ────────────────────────────
  Widget _mobileBody(BuildContext context) {
    final isLoading = ref.watch(authProvider).isLoading;
    return SafeArea(
      child: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(child: _MobileHeader(onBack: () => context.pop())),
          SliverPadding(
            padding: const EdgeInsets.all(24),
            sliver: SliverToBoxAdapter(
              child: _buildFormContent(context, isLoading),
            ),
          ),
        ],
      ),
    );
  }

  // ── Wide body (tablet / desktop) ───────────────────────────────────────
  Widget _wideBody(BuildContext context) {
    final isLoading = ref.watch(authProvider).isLoading;
    return SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: EdgeInsets.symmetric(
            horizontal: context.isDesktop ? 48 : 32,
            vertical: 40,
          ),
          child: ConstrainedBox(
            constraints:
                const BoxConstraints(maxWidth: Breakpoints.formMaxWidth),
            child: Column(
              children: [
                // Card header with back button
                Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.arrow_back),
                      color: AppColors.textPrimary,
                      onPressed: () => context.pop(),
                    ),
                    const SizedBox(width: 4),
                    const _CompactBrand(),
                  ],
                ),
                const SizedBox(height: 24),

                // Form card
                Container(
                  padding: const EdgeInsets.all(36),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.border),
                    boxShadow: const [
                      BoxShadow(
                        color: AppColors.cardShadow,
                        blurRadius: 24,
                        offset: Offset(0, 8),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Create Account',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Join SpectraGuard today',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                      const SizedBox(height: 28),
                      _buildFormContent(context, isLoading),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ── Form content (shared between mobile and wide) ─────────────────────
  Widget _buildFormContent(BuildContext context, bool isLoading) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _SectionLabel('Personal Information'),
          const SizedBox(height: 12),
          _field(_nameCtrl, 'Full Name', Icons.person_outlined,
              validator: (v) =>
                  v == null || v.isEmpty ? 'Required' : null),
          const SizedBox(height: 14),
          _field(_emailCtrl, 'Email', Icons.email_outlined,
              keyboard: TextInputType.emailAddress,
              validator: (v) =>
                  v == null || !v.contains('@') ? 'Invalid email' : null),
          const SizedBox(height: 14),
          TextFormField(
            controller: _passwordCtrl,
            obscureText: _obscure,
            style: const TextStyle(color: AppColors.textPrimary),
            decoration: InputDecoration(
              labelText: 'Password',
              prefixIcon: const Icon(Icons.lock_outlined),
              suffixIcon: IconButton(
                icon: Icon(
                    _obscure ? Icons.visibility_off : Icons.visibility),
                onPressed: () =>
                    setState(() => _obscure = !_obscure),
              ),
            ),
            validator: (v) =>
                v == null || v.length < 8 ? 'Min 8 characters' : null,
          ),
          const SizedBox(height: 14),
          _field(_phoneCtrl, 'Phone (optional)', Icons.phone_outlined,
              keyboard: TextInputType.phone),
          const SizedBox(height: 22),

          _SectionLabel('Role & Organisation'),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: _role,
            dropdownColor: AppColors.surfaceElevated,
            style: const TextStyle(color: AppColors.textPrimary),
            decoration: const InputDecoration(
              labelText: 'Role',
              prefixIcon: Icon(Icons.badge_outlined),
            ),
            items: _roles
                .map((r) => DropdownMenuItem(
                      value: r,
                      child: Text(r[0].toUpperCase() + r.substring(1)),
                    ))
                .toList(),
            onChanged: (v) =>
                setState(() => _role = v ?? 'public'),
          ),
          const SizedBox(height: 14),
          _field(_orgCtrl, 'Organization (optional)',
              Icons.business_outlined),
          if (_needsLicense) ...[
            const SizedBox(height: 14),
            _field(
              _licenseCtrl,
              'License Number',
              Icons.card_membership_outlined,
              validator: (v) =>
                  _needsLicense && (v == null || v.isEmpty)
                      ? 'Required for this role'
                      : null,
            ),
            const SizedBox(height: 14),
            _field(_designationCtrl, 'Designation',
                Icons.work_outlined),
          ],
          const SizedBox(height: 14),
          _field(_cityCtrl, 'City (optional)',
              Icons.location_city_outlined),
          const SizedBox(height: 32),

          _GradientButton(
            onPressed: isLoading ? null : _submit,
            child: isLoading
                ? const SizedBox(
                    height: 22,
                    width: 22,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: Colors.white),
                  )
                : const Text(
                    'Create Account',
                    style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: Colors.white),
                  ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Already have an account?',
                  style: Theme.of(context).textTheme.bodyMedium),
              TextButton(
                onPressed: () => context.pop(),
                child: const Text('Sign In'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _field(
    TextEditingController ctrl,
    String label,
    IconData icon, {
    TextInputType? keyboard,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: ctrl,
      keyboardType: keyboard,
      style: const TextStyle(color: AppColors.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
      ),
      validator: validator,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Mobile gradient header (original)
// ─────────────────────────────────────────────────────────────────────────────

class _MobileHeader extends StatelessWidget {
  const _MobileHeader({required this.onBack});
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [AppColors.gradientStart, AppColors.gradientEnd],
        ),
        borderRadius: BorderRadius.only(
          bottomLeft: Radius.circular(28),
          bottomRight: Radius.circular(28),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          IconButton(
            icon: const Icon(Icons.arrow_back, color: Colors.white),
            onPressed: onBack,
            padding: EdgeInsets.zero,
          ),
          const SizedBox(height: 8),
          const Text(
            'Create Account',
            style: TextStyle(
              color: Colors.white,
              fontSize: 26,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Join SpectraGuard today',
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.8),
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

class _CompactBrand extends StatelessWidget {
  const _CompactBrand();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppColors.gradientStart, AppColors.gradientEnd],
            ),
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Icon(Icons.biotech, color: Colors.white, size: 20),
        ),
        const SizedBox(width: 10),
        const Text(
          'SpectraGuard',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
      ],
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 3,
          height: 16,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [AppColors.gradientStart, AppColors.gradientEnd],
            ),
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          text,
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _GradientButton extends StatelessWidget {
  const _GradientButton({required this.child, required this.onPressed});
  final Widget child;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: onPressed == null
              ? LinearGradient(colors: [
                  AppColors.primary.withValues(alpha: 0.5),
                  AppColors.primaryDark.withValues(alpha: 0.5),
                ])
              : const LinearGradient(
                  colors: [AppColors.gradientStart, AppColors.gradientEnd]),
          borderRadius: BorderRadius.circular(12),
        ),
        child: ElevatedButton(
          onPressed: onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.transparent,
            shadowColor: Colors.transparent,
            foregroundColor: Colors.white,
            minimumSize: const Size(double.infinity, 52),
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12)),
          ),
          child: child,
        ),
      ),
    );
  }
}
