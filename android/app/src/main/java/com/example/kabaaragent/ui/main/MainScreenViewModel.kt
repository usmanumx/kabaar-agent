package com.example.kabaaragent.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.kabaaragent.data.DataRepository
import com.example.kabaaragent.data.PipelineResponse
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class MainUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val response: PipelineResponse? = null,
    val terminalLogs: List<String> = listOf("SYSTEM: KabaarAgent Terminal Initialized. Ready for input..."),
    val inputDescription: String = ""
)

class MainScreenViewModel(private val dataRepository: DataRepository) : ViewModel() {

    private val _uiState = MutableStateFlow(MainUiState())
    val uiState: StateFlow<MainUiState> = _uiState.asStateFlow()

    private var logPrintJob: Job? = null

    fun onDescriptionChange(newDesc: String) {
        _uiState.update { it.copy(inputDescription = newDesc) }
    }

    fun mockCameraInput() {
        _uiState.update {
            it.copy(
                inputDescription = "High-grade copper tubing (approx 4.5kg) & clean brass fittings (2.0kg)",
                terminalLogs = it.terminalLogs + "UI: Mock camera triggered. Captured image analyzed locally. Pre-filled description."
            )
        }
    }

    fun mockVoiceInput() {
        _uiState.update {
            it.copy(
                inputDescription = "Identify 8 kilograms of lead-acid scrap batteries and a small box of aluminum cans",
                terminalLogs = it.terminalLogs + "UI: Voice recording finished. Transcribed description via Whisper-API."
            )
        }
    }

    fun processScrap(description: String = _uiState.value.inputDescription) {
        if (description.isBlank()) {
            _uiState.update { it.copy(error = "Please enter a description or use a mock trigger first.") }
            return
        }

        logPrintJob?.cancel()
        _uiState.update {
            it.copy(
                isLoading = true,
                error = null,
                response = null,
                terminalLogs = listOf(
                    "UI: Initiating transaction appraisal pipeline...",
                    "UI: Connecting to backend server at http://10.0.2.2:8000...",
                    "UI: Sending payload: description='$description'"
                )
            )
        }

        viewModelScope.launch {
            try {
                val result = dataRepository.processScrap(description)
                _uiState.update { it.copy(isLoading = false, response = result) }
                // Print execution trace line-by-line for premium dynamic feeling
                animateTerminalLogs(result.execution_trace)
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.localizedMessage ?: "Unknown connection error",
                        terminalLogs = it.terminalLogs + listOf(
                            "ERROR: Failed to connect to FastAPI server.",
                            "ERROR: Please ensure backend is running at http://127.0.0.1:8000.",
                            "DETAILS: ${e.message}"
                        )
                    )
                }
            }
        }
    }

    private fun animateTerminalLogs(logs: List<String>) {
        logPrintJob = viewModelScope.launch {
            for (log in logs) {
                delay(300) // 300ms delay between each trace line
                _uiState.update { it.copy(terminalLogs = it.terminalLogs + log) }
            }
            _uiState.update { it.copy(terminalLogs = it.terminalLogs + "SYSTEM: Pipeline execution trace complete.") }
        }
    }
}
