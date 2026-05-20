package com.example.kabaaragent.ui.main

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.kabaaragent.data.DefaultDataRepository
import com.example.kabaaragent.data.ItemModel
import com.example.kabaaragent.data.PipelineResponse
import com.example.kabaaragent.theme.KabaarAgentTheme
import com.example.kabaaragent.theme.Purple80

// Sleek dark palette overrides
val DarkBg = Color(0xFF0F172A)
val CardBg = Color(0xFF1E293B)
val BorderColor = Color(0xFF334155)
val AccentCyan = Color(0xFF06B6D4)
val AccentGreen = Color(0xFF10B981)
val AccentPurple = Color(0xFF6366F1)
val AccentAmber = Color(0xFFF59E0B)
val ConsoleBg = Color(0xFF030712)
val TextLight = Color(0xFFF8FAFC)
val TextMuted = Color(0xFF94A3B8)

@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: MainScreenViewModel = viewModel { MainScreenViewModel(DefaultDataRepository()) },
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    MainScreenContent(
        state = state,
        onDescriptionChange = { viewModel.onDescriptionChange(it) },
        onMockCamera = { viewModel.mockCameraInput() },
        onMockVoice = { viewModel.mockVoiceInput() },
        onRunAppraisal = { viewModel.processScrap() },
        modifier = modifier
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreenContent(
    state: MainUiState,
    onDescriptionChange: (String) -> Unit,
    onMockCamera: () -> Unit,
    onMockVoice: () -> Unit,
    onRunAppraisal: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBg)
            .padding(16.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // App Header
        AppHeader()

        // Valuation Banner
        ValuationBanner(
            response = state.response,
            isLoading = state.isLoading
        )

        // Control Panel (mock triggers & input)
        ControlPanel(
            description = state.inputDescription,
            onDescriptionChange = onDescriptionChange,
            onMockCamera = onMockCamera,
            onMockVoice = onMockVoice,
            onRunAppraisal = onRunAppraisal,
            isLoading = state.isLoading
        )

        // Itemized Breakdown (if response is available)
        AnimatedVisibility(
            visible = state.response != null && state.response.items.isNotEmpty(),
            enter = fadeIn(),
            exit = fadeOut()
        ) {
            ItemizedBreakdownSection(items = state.response?.items ?: emptyList())
        }

        // Live Execution Trace Terminal
        TerminalPane(
            logs = state.terminalLogs,
            isLoading = state.isLoading
        )
        
        Spacer(modifier = Modifier.height(24.dp))
    }
}

@Composable
fun AppHeader() {
    Column(modifier = Modifier.fillMaxWidth()) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.fillMaxWidth()
        ) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .background(AccentCyan, shape = CircleShape)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "KABAAR AGENT",
                style = TextStyle(
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    color = Color.White
                )
            )
            Spacer(modifier = Modifier.weight(1f))
            Box(
                modifier = Modifier
                    .background(AccentPurple.copy(alpha = 0.2f), shape = RoundedCornerShape(4.dp))
                    .border(1.dp, AccentPurple, shape = RoundedCornerShape(4.dp))
                    .padding(horizontal = 6.dp, vertical = 2.dp)
            ) {
                Text(
                    text = "ANTIGRAVITY 2.0 SDK",
                    style = TextStyle(
                        fontWeight = FontWeight.Bold,
                        fontSize = 10.sp,
                        color = Purple80
                    )
                )
            }
        }
        Text(
            text = "AI-Driven Scrap Appraisal & Ledger Network Client",
            style = TextStyle(
                fontSize = 12.sp,
                color = TextMuted
            ),
            modifier = Modifier.padding(start = 18.dp, top = 2.dp)
        )
    }
}

@Composable
fun ValuationBanner(
    response: PipelineResponse?,
    isLoading: Boolean
) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val alphaAnim by infiniteTransition.animateFloat(
        initialValue = 0.6f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )

    val gradient = Brush.horizontalGradient(
        colors = listOf(AccentCyan, AccentGreen)
    )

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(
                width = 1.dp,
                brush = Brush.linearGradient(listOf(BorderColor, AccentCyan.copy(alpha = 0.4f))),
                shape = RoundedCornerShape(12.dp)
            ),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = CardBg)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "ESTIMATED VALUATION",
                style = TextStyle(
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = TextMuted,
                    letterSpacing = 1.5.sp
                )
            )

            Spacer(modifier = Modifier.height(8.dp))

            if (isLoading) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = AccentCyan,
                        strokeWidth = 2.dp
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text = "Appraising Scrap...",
                        style = TextStyle(
                            fontSize = 24.sp,
                            fontWeight = FontWeight.Bold,
                            color = TextLight
                        ),
                        modifier = Modifier.alpha(alphaAnim)
                    )
                }
            } else if (response != null) {
                Text(
                    text = "$${String.format("%.2f", response.valuation)}",
                    style = TextStyle(
                        brush = gradient,
                        fontSize = 42.sp,
                        fontWeight = FontWeight.ExtraBold
                    )
                )

                Spacer(modifier = Modifier.height(4.dp))

                val yardName = response.optimal_yard?.get("name")?.toString()?.replace("\"", "") ?: "N/A"
                val distance = response.optimal_yard?.get("distance_km")?.toString() ?: "0.0"

                Text(
                    text = "Optimal Match: $yardName ($distance km away)",
                    style = TextStyle(
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                        color = AccentGreen
                    )
                )

                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Transaction Signed & Committed to Ledger",
                    style = TextStyle(
                        fontFamily = FontFamily.Monospace,
                        fontSize = 10.sp,
                        color = AccentCyan
                    )
                )
            } else {
                Text(
                    text = "$0.00",
                    style = TextStyle(
                        fontSize = 36.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextLight.copy(alpha = 0.5f)
                    )
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Awaiting input scan or appraisal...",
                    style = TextStyle(
                        fontSize = 13.sp,
                        color = TextMuted
                    )
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ControlPanel(
    description: String,
    onDescriptionChange: (String) -> Unit,
    onMockCamera: () -> Unit,
    onMockVoice: () -> Unit,
    onRunAppraisal: () -> Unit,
    isLoading: Boolean
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, BorderColor, RoundedCornerShape(12.dp)),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = CardBg)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = "INPUT Appraisal Control Panel",
                style = TextStyle(
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = TextLight
                )
            )

            // Trigger Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Mock Camera
                Button(
                    onClick = onMockCamera,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = AccentPurple),
                    enabled = !isLoading
                ) {
                    Text("📸 Camera Mock", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }

                // Mock Voice
                Button(
                    onClick = onMockVoice,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = AccentCyan),
                    enabled = !isLoading
                ) {
                    Text("🎙️ Voice Mock", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }

            // Description Input
            OutlinedTextField(
                value = description,
                onValueChange = onDescriptionChange,
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("Describe scrap materials or trigger mock capture...", color = TextMuted) },
                maxLines = 4,
                textStyle = TextStyle(color = TextLight, fontSize = 14.sp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = AccentCyan,
                    unfocusedBorderColor = BorderColor,
                    focusedContainerColor = ConsoleBg,
                    unfocusedContainerColor = ConsoleBg.copy(alpha = 0.5f)
                ),
                shape = RoundedCornerShape(8.dp)
            )

            // CTA Button
            Button(
                onClick = onRunAppraisal,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AccentGreen,
                    disabledContainerColor = AccentGreen.copy(alpha = 0.5f)
                ),
                enabled = !isLoading && description.isNotBlank()
            ) {
                Text(
                    text = if (isLoading) "Running Appraisal..." else "🚀 RUN PIPELINE APPRAISAL",
                    fontWeight = FontWeight.ExtraBold,
                    color = Color.White
                )
            }
        }
    }
}

@Composable
fun ItemizedBreakdownSection(items: List<ItemModel>) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, BorderColor, RoundedCornerShape(12.dp)),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = CardBg)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Itemized Breakdown",
                style = TextStyle(
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = TextLight
                )
            )

            HorizontalDivider(color = BorderColor)

            items.forEach { item ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(ConsoleBg, RoundedCornerShape(6.dp))
                        .padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .background(AccentGreen.copy(alpha = 0.15f), shape = CircleShape)
                            .padding(4.dp)
                    ) {
                        Text("✓", color = AccentGreen, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = item.material_type.replaceFirstChar { it.uppercase() },
                            style = TextStyle(
                                fontWeight = FontWeight.Bold,
                                color = TextLight,
                                fontSize = 14.sp
                            )
                        )
                        Text(
                            text = "Grade: ${item.purity_grade}",
                            style = TextStyle(
                                color = TextMuted,
                                fontSize = 11.sp
                            )
                        )
                    }
                    Text(
                        text = "${item.estimated_weight_kg} kg",
                        style = TextStyle(
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            color = AccentCyan,
                            fontSize = 14.sp
                        )
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Box(
                        modifier = Modifier
                            .background(AccentGreen.copy(alpha = 0.2f), shape = RoundedCornerShape(4.dp))
                            .padding(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = "Verified",
                            style = TextStyle(
                                fontWeight = FontWeight.Bold,
                                fontSize = 9.sp,
                                color = AccentGreen
                            )
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun TerminalPane(
    logs: List<String>,
    isLoading: Boolean
) {
    val listState = rememberLazyListState()

    // Auto scroll to latest logs
    LaunchedEffect(logs.size) {
        if (logs.isNotEmpty()) {
            listState.animateScrollToItem(logs.size - 1)
        }
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .height(200.dp)
            .border(1.dp, BorderColor, RoundedCornerShape(12.dp)),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = ConsoleBg)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth()
            ) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .background(if (isLoading) AccentAmber else AccentGreen, shape = CircleShape)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "EXECUTION TRACE LOGS",
                    style = TextStyle(
                        fontFamily = FontFamily.Monospace,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = if (isLoading) AccentAmber else AccentGreen
                    )
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            LazyColumn(
                state = listState,
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                items(logs) { log ->
                    val color = when {
                        log.startsWith("ERROR:") -> Color(0xFFEF4444)
                        log.startsWith("UI:") -> AccentPurple
                        log.startsWith("SYSTEM:") -> AccentCyan
                        else -> TextLight
                    }
                    Text(
                        text = log,
                        style = TextStyle(
                            fontFamily = FontFamily.Monospace,
                            fontSize = 10.sp,
                            color = color
                        )
                    )
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun MainScreenPreview() {
    KabaarAgentTheme {
        MainScreenContent(
            state = MainUiState(
                inputDescription = "Copper pipe 5kg",
                terminalLogs = listOf("SYSTEM: Ready")
            ),
            onDescriptionChange = {},
            onMockCamera = {},
            onMockVoice = {},
            onRunAppraisal = {}
        )
    }
}
