import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:spectra_app/core/api/api_client.dart';
import 'package:spectra_app/core/theme/app_theme.dart';
import 'package:spectra_app/core/utils/responsive.dart';

// ─── Message model ────────────────────────────────────────────────────────────

enum _Sender { user, bot }

class _Message {
  _Message({required this.sender, required this.text, DateTime? time})
      : time = time ?? DateTime.now();
  final _Sender sender;
  final String text;
  final DateTime time;
}

// ─── Rule-based fallback ──────────────────────────────────────────────────────

String _botReply(String input) {
  final q = input.toLowerCase().trim();

  if (q.contains('genuine') || q.contains('authentic')) {
    return 'A sample is classified as **Genuine** when its cosine similarity '
        'against the reference spectrum is ≥ 97% (0.970). This confirms that '
        'the spectral fingerprint matches the authenticated reference compound, '
        'verifying both the presence and proper ratio of the Active Pharmaceutical Ingredient (API).';
  }
  if (q.contains('counterfeit') || q.contains('fake')) {
    return 'A **Potentially Counterfeit** result is returned when the cosine similarity '
        'falls below 85% (< 0.850). This indicates missing diagnostic peaks, significant '
        'wavenumber shifts, or foreign spectral artifacts. **Action:** Quarantine the batch '
        'immediately, log the serial number, and send a sample for confirmatory HPLC / LC-MS analysis.';
  }
  if (q.contains('borderline') || q.contains('verification') || q.contains('verify')) {
    return 'A **Requires Verification** result (85% – 97% similarity) is borderline. '
        'This may stem from minor excipient variations, batch-to-batch manufacturing shifts, '
        'or early sample degradation. We recommend secondary laboratory verification (HPLC or dissolution testing) '
        'before releasing the lot.';
  }
  if (q.contains('cosine') || q.contains('similarity')) {
    return 'Cosine similarity calculates the dot product of normalized spectral vectors:\n'
        '• Formula: Sim(A, B) = (A · B) / (||A|| × ||B||)\n\n'
        'A score of 1.000 means identical spectra. SpectraGuard thresholds:\n'
        '• **≥ 0.970**: Genuine\n'
        '• **0.850 – 0.969**: Requires Verification\n'
        '• **< 0.850**: Potentially Counterfeit';
  }
  if (q.contains('raman') || q.contains('spectroscop')) {
    return 'Raman Spectroscopy is a high-precision, non-destructive optical technique. '
        'When monochromatic laser light interacts with molecular bonds, inelastic scattering '
        '(Raman shift) occurs. The resulting wavenumber spectrum (cm⁻¹) acts as a unique '
        'chemical fingerprint capable of identifying APIs and excipients in seconds.';
  }
  if (q.contains('upload') || q.contains('csv')) {
    return 'To run a test, navigate to **Upload Spectra** and select a CSV file. '
        'Format requirement:\n'
        '• Column 1: Wavenumber (cm⁻¹)\n'
        '• Column 2: Intensity (arbitrary units)\n'
        'SpectraGuard automatically performs baseline correction, noise filtering, and intensity normalization.';
  }
  if (q.contains('report') || q.contains('pdf')) {
    return 'PDF reports can be downloaded from any Test Details screen. Reports contain:\n'
        '1. Classification status & risk assessment\n'
        '2. Match score & cosine similarity breakdown\n'
        '3. High-resolution spectral overlay charts\n'
        '4. Prominent peak alignment tables (cm⁻¹ shifts)\n'
        '5. AI diagnostic rationale & regulatory compliance stamps';
  }
  if (q.contains('hello') || q.contains('hi') || q.contains('hey')) {
    return 'Hello! I\'m your SpectraGuard AI Assistant. Ask me anything about '
        'pharmaceutical testing, Raman spectroscopy, cosine similarity, or how to handle suspect samples!';
  }
  if (q.contains('help') || q.contains('what can you')) {
    return 'I can assist you with:\n'
        '• **Classification**: Genuine vs Counterfeit thresholds\n'
        '• **Spectral Math**: Cosine similarity & peak prominence\n'
        '• **Preprocessing**: Baseline correction & SNR analysis\n'
        '• **App Usage**: Uploading CSVs & exporting PDF reports\n'
        '• **Protocols**: Quarantine steps & regulatory reporting\n\n'
        'Feel free to type your question or select a suggested topic below!';
  }

  return 'I don\'t have a direct answer for that specific phrasing, but I can help with '
      'classification rules, cosine similarity, Raman spectroscopy, uploading CSVs, or PDF reporting. '
      'Type **help** to see all available topics.';
}

// ─── Provider (User-Isolated AutoDispose) ────────────────────────────────────

final _chatMessagesProvider =
    StateNotifierProvider.autoDispose<_ChatNotifier, List<_Message>>(
  (ref) => _ChatNotifier(),
);

class _ChatNotifier extends StateNotifier<List<_Message>> {
  _ChatNotifier()
      : super([
          _Message(
            sender: _Sender.bot,
            text: 'Hi! I\'m your SpectraGuard AI Assistant powered by Gemini. Ask me anything about '
                'drug authentication, spectral analysis, or how to use the app.',
          ),
        ]) {
    fetchHistory();
  }

  Future<void> fetchHistory() async {
    try {
      final dio = createDio();
      final response = await dio.get('/chat/messages');
      final data = response.data as List;
      if (data.isNotEmpty) {
        final list = <_Message>[];
        for (final item in data) {
          list.add(_Message(
            sender: item['sender'] == 'user' ? _Sender.user : _Sender.bot,
            text: item['text'] as String,
          ));
        }
        state = list;
      }
    } catch (_) {
      // Keep initial welcoming message if endpoint is unreachable or history empty
    }
  }

  Future<void> send(String text) async {
    if (text.trim().isEmpty) return;
    final trimmed = text.trim();

    // Optimistically push user message
    state = [
      ...state,
      _Message(sender: _Sender.user, text: trimmed),
    ];

    try {
      final dio = createDio();
      final response = await dio.post(
        '/chat/message',
        data: {'message': trimmed},
      );
      final replyText = response.data['text'] as String;
      state = [
        ...state,
        _Message(sender: _Sender.bot, text: replyText),
      ];
    } catch (_) {
      // Fallback reply if offline or API error
      state = [
        ...state,
        _Message(sender: _Sender.bot, text: _botReply(trimmed)),
      ];
    }
  }

  Future<void> clear() async {
    try {
      final dio = createDio();
      await dio.delete('/chat/messages');
    } catch (_) {}
    state = [
      _Message(
        sender: _Sender.bot,
        text: 'Chat cleared. How can I help you?',
      ),
    ];
  }
}

// ─── Screen ───────────────────────────────────────────────────────────────────

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _ctrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  @override
  void initState() {
    super.initState();
    // Ensure history is re-fetched when screen is opened
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(_chatMessagesProvider.notifier).fetchHistory();
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _send() {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    _ctrl.clear();
    ref.read(_chatMessagesProvider.notifier).send(text);
    Future.delayed(const Duration(milliseconds: 300), _scrollToBottom);
  }

  void _scrollToBottom() {
    if (_scrollCtrl.hasClients) {
      _scrollCtrl.animateTo(
        _scrollCtrl.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(_chatMessagesProvider);
    final cs = Theme.of(context).colorScheme;

    // Auto-scroll when new messages arrive
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Column(
        children: [
          _ChatHeader(
            onClear: () => ref.read(_chatMessagesProvider.notifier).clear(),
          ),
          Expanded(
            child: ContentContainer(
              maxWidth: 760,
              child: ListView.builder(
                controller: _scrollCtrl,
                padding: const EdgeInsets.symmetric(
                    horizontal: 16, vertical: 16),
                itemCount: messages.length,
                itemBuilder: (_, i) => _MessageBubble(msg: messages[i]),
              ),
            ),
          ),
          _SuggestedChips(onTap: (s) {
            _ctrl.text = s;
            _send();
          }),
          _InputBar(
            controller: _ctrl,
            onSend: _send,
            cs: cs,
          ),
        ],
      ),
    );
  }
}

// ─── Chat header ──────────────────────────────────────────────────────────────

class _ChatHeader extends StatelessWidget {
  const _ChatHeader({required this.onClear});
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: cs.surface,
        border: Border(bottom: BorderSide(color: cs.outline)),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 8, 16),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.smart_toy_outlined,
                    color: AppColors.primary, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'AI Assistant',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w700,
                        color: cs.onSurface,
                      ),
                    ),
                    Text(
                      'Powered by Gemini AI',
                      style: TextStyle(
                          fontSize: 12, color: cs.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'Clear chat',
                icon: Icon(Icons.delete_sweep_outlined,
                    color: cs.onSurfaceVariant),
                onPressed: onClear,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Message bubble ───────────────────────────────────────────────────────────

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.msg});
  final _Message msg;

  @override
  Widget build(BuildContext context) {
    final isUser = msg.sender == _Sender.user;
    final cs = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!isUser) ...[
            Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.smart_toy_outlined,
                  color: AppColors.primary, size: 15),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isUser
                    ? AppColors.primary
                    : cs.surface,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(isUser ? 16 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 16),
                ),
                border: isUser
                    ? null
                    : Border.all(color: cs.outline),
                boxShadow: [
                  BoxShadow(
                    color: cs.shadow.withOpacity(0.04),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: _RichText(
                text: msg.text,
                baseStyle: TextStyle(
                  fontSize: 14,
                  height: 1.45,
                  color: isUser ? Colors.white : cs.onSurface,
                ),
                boldStyle: TextStyle(
                  fontSize: 14,
                  height: 1.45,
                  fontWeight: FontWeight.w700,
                  color: isUser ? Colors.white : AppColors.primary,
                ),
              ),
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }
}

/// Parses **bold** markdown and renders mixed spans.
class _RichText extends StatelessWidget {
  const _RichText({
    required this.text,
    required this.baseStyle,
    required this.boldStyle,
  });
  final String text;
  final TextStyle baseStyle;
  final TextStyle boldStyle;

  @override
  Widget build(BuildContext context) {
    final spans = <InlineSpan>[];
    final regex = RegExp(r'\*\*(.+?)\*\*');
    int last = 0;
    for (final m in regex.allMatches(text)) {
      if (m.start > last) {
        spans.add(TextSpan(
            text: text.substring(last, m.start), style: baseStyle));
      }
      spans.add(TextSpan(text: m.group(1), style: boldStyle));
      last = m.end;
    }
    if (last < text.length) {
      spans.add(TextSpan(text: text.substring(last), style: baseStyle));
    }
    return Text.rich(TextSpan(children: spans));
  }
}

// ─── Suggested chips ──────────────────────────────────────────────────────────

class _SuggestedChips extends StatelessWidget {
  const _SuggestedChips({required this.onTap});
  final ValueChanged<String> onTap;

  static const _suggestions = [
    'What is cosine similarity?',
    'How do I upload spectra?',
    'What does counterfeit mean?',
    'Explain Raman spectroscopy',
    'What is a Genuine classification?',
    'What is Requires Verification?',
    'How are peak wavenumbers analyzed?',
    'What is spectral baseline correction?',
    'How do I export PDF reports?',
    'What is the risk rating scale?',
    'How to handle suspected fake drugs?',
    'What secondary lab tests are recommended?',
    'How does the Reference DB work?',
    'What is signal-to-noise ratio (SNR)?',
    'How do I report fake medicines to authorities?',
    'What active ingredients are supported?',
  ];

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      height: 44,
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: cs.outline.withOpacity(0.5))),
      ),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        itemCount: _suggestions.length,
        itemBuilder: (_, i) {
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: GestureDetector(
              onTap: () => onTap(_suggestions[i]),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                      color: AppColors.primary.withOpacity(0.25)),
                ),
                child: Text(
                  _suggestions[i],
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                    color: AppColors.primary,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

// ─── Input bar ────────────────────────────────────────────────────────────────

class _InputBar extends StatelessWidget {
  const _InputBar({
    required this.controller,
    required this.onSend,
    required this.cs,
  });
  final TextEditingController controller;
  final VoidCallback onSend;
  final ColorScheme cs;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: cs.surface,
        border: Border(top: BorderSide(color: cs.outline)),
      ),
      padding: EdgeInsets.fromLTRB(
          16, 10, 10, 10 + MediaQuery.viewInsetsOf(context).bottom),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                onSubmitted: (_) => onSend(),
                textInputAction: TextInputAction.send,
                maxLines: 4,
                minLines: 1,
                style: TextStyle(fontSize: 14, color: cs.onSurface),
                decoration: InputDecoration(
                  hintText: 'Ask me anything...',
                  hintStyle: TextStyle(
                      color: cs.onSurfaceVariant.withOpacity(0.6)),
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide(color: cs.outline),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide(color: cs.outline),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: const BorderSide(
                        color: AppColors.primary, width: 1.5),
                  ),
                  filled: true,
                  fillColor: cs.surface,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                color: AppColors.primary,
                shape: BoxShape.circle,
              ),
              child: IconButton(
                icon: const Icon(Icons.send_rounded,
                    color: Colors.white, size: 18),
                onPressed: onSend,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
