#include "llama.cpp/llama.h"   // Zależność do llama.cpp
#include "cpp-httplib/httplib.h"  // Zależność do cpp-httplib
#include <fstream>
#include <iostream>

using namespace httplib;

// Funkcja obsługująca model LLaMA
std::string process_request(const std::string& prompt) {
    llama_context* ctx;
    llama_context_params params = llama_context_default_params();

    // Załaduj skwantyzowany model LLaMA
    const std::string model_path = "models/llama-3.1-1b-q4.bin";
    ctx = llama_init_from_file(model_path.c_str(), params);

    if (!ctx) {
        std::cerr << "Nie można załadować modelu!" << std::endl;
        return "";
    }

    // Przetwarzanie prompta przez model
    std::vector<llama_token> tokens = llama_tokenize(ctx, prompt.c_str(), true);
    llama_eval(ctx, tokens.data(), tokens.size(), 0, params.n_threads);

    std::string response;
    for (int i = 0; i < 50; ++i) {
        llama_token token = llama_sample_next(ctx);
        response += llama_token_to_str(ctx, token);
    }

    llama_free(ctx);
    return response;
}

// Funkcja do zapisywania zapytań i odpowiedzi
void log_request(const std::string& prompt, const std::string& response) {
    std::ofstream log_file("requests.log", std::ios::app);
    log_file << "Prompt: " << prompt << "\n";
    log_file << "Response: " << response << "\n";
    log_file << "---------------------\n";
    log_file.close();
}

int main() {
    // Tworzenie serwera
    Server svr;

    svr.Post("/api/zapytanie", [&](const Request& req, Response& res) {
        // Pobieranie prompta z żądania JSON
        auto prompt = req.body;

        // Przetwarzanie zapytania przez model LLaMA
        std::string response = process_request(prompt);

        // Zapis zapytania i odpowiedzi do pliku
        log_request(prompt, response);

        // Odpowiedź na zapytanie
        res.set_content(response, "text/plain");
    });

    std::cout << "Serwer działa na porcie 8080..." << std::endl;
    svr.listen("0.0.0.0", 8080);

    return 0;
}
